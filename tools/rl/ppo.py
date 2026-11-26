"""PPO in numpy for the Shadow Masque rival (docs/final/RL_POLICY.md, task T07).

Two tanh MLPs (actor over the 9 macro slots, critic to a scalar), masked
softmax, GAE, clipped objective, Adam. Training only: the game runs the
exported actor with pure-Python inference (agents/rl/policy.py)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

from agents.rl.encoder import MACRO_SLOTS
from agents.rl.policy import FORMAT

NEG = -1e9


# ---------------------------------------------------------------- parameters
def _mlp(sizes, rng, last_scale):
    layers = []
    for i, (a, b) in enumerate(zip(sizes, sizes[1:])):
        scale = last_scale if i == len(sizes) - 2 else np.sqrt(2.0 / a)
        layers.append([rng.standard_normal((a, b)) * scale, np.zeros(b)])
    return layers


def init_params(sizes, seed: int) -> dict:
    """`sizes` = (features, hidden..., macros). The critic shares the hidden sizes."""
    rng = np.random.default_rng(seed)
    return {"sizes": tuple(sizes),
            "actor": _mlp(sizes, rng, 0.01),
            "critic": _mlp(tuple(sizes[:-1]) + (1,), rng, 1.0),
            "opt": {"t": 0, "m": {}, "v": {}}}


def _forward(layers, x):
    acts = [x]
    h = x
    for i, (w, b) in enumerate(layers):
        z = h @ w + b
        h = z if i == len(layers) - 1 else np.tanh(z)
        acts.append(h)
    return acts


def actor_logits(params, x):
    return _forward(params["actor"], np.asarray(x, float))[-1]


def critic_value(params, x):
    return _forward(params["critic"], np.asarray(x, float))[-1][:, 0]


def _masked_log_softmax(z, mask):
    z = np.where(mask, z, NEG)
    z = z - z.max(axis=1, keepdims=True)
    e = np.exp(z) * mask
    return z - np.log(e.sum(axis=1, keepdims=True))


def logp(params, x, mask, acts):
    lp = _masked_log_softmax(actor_logits(params, x), mask)
    return lp[np.arange(len(acts)), acts]


def gae(rewards, values, last_value, gamma, lam):
    n = len(rewards)
    adv = np.zeros(n)
    nxt, nxt_v = 0.0, last_value
    for t in range(n - 1, -1, -1):
        delta = rewards[t] + gamma * nxt_v - values[t]
        nxt = delta + gamma * lam * nxt
        adv[t] = nxt
        nxt_v = values[t]
    return adv, adv + np.asarray(values)


# ------------------------------------------------------------------- update
def _backward(layers, acts, grad_out):
    """Gradients of each layer given d loss / d output."""
    grads = []
    g = grad_out
    for i in range(len(layers) - 1, -1, -1):
        w, _ = layers[i]
        grads.append((acts[i].T @ g, g.sum(axis=0)))
        if i > 0:
            g = (g @ w.T) * (1.0 - acts[i] ** 2)
    return grads[::-1]


def _adam(params, key, layers, grads, lr, max_norm):
    opt = params["opt"]
    flat = [g for gw, gb in grads for g in (gw, gb)]
    norm = np.sqrt(sum(float((g ** 2).sum()) for g in flat))
    scale = min(1.0, max_norm / (norm + 1e-12))
    opt["t"] += 1 if key == "actor" else 0
    t = max(opt["t"], 1)
    for i, ((w, b), (gw, gb)) in enumerate(zip(layers, grads)):
        for j, (p, g) in enumerate(((w, gw), (b, gb))):
            k = (key, i, j)
            m = opt["m"].setdefault(k, np.zeros_like(p))
            v = opt["v"].setdefault(k, np.zeros_like(p))
            g = g * scale
            m *= 0.9; m += 0.1 * g
            v *= 0.999; v += 0.001 * g * g
            p -= lr * (m / (1 - 0.9 ** t)) / (np.sqrt(v / (1 - 0.999 ** t)) + 1e-8)


def update(params, batch, lr, clip, epochs, minibatch, vf, ent, seed, max_norm=0.5) -> dict:
    """In-place PPO update on one batch {x, mask, a, logp, adv, ret}."""
    rng = np.random.default_rng(seed)
    n = len(batch["a"])
    stats = {"policy_loss": 0.0, "value_loss": 0.0, "entropy": 0.0, "clip_frac": 0.0}
    count = 0
    for _ in range(epochs):
        order = rng.permutation(n)
        for s in range(0, n, minibatch):
            idx = order[s:s + minibatch]
            x, mask, a = batch["x"][idx], batch["mask"][idx], batch["a"][idx]
            adv, ret, old = batch["adv"][idx], batch["ret"][idx], batch["logp"][idx]
            m = len(idx)
            acts = _forward(params["actor"], x)
            lp_all = _masked_log_softmax(acts[-1], mask)
            p = np.exp(lp_all) * mask
            lp = lp_all[np.arange(m), a]
            ratio = np.exp(lp - old)
            clipped = (ratio < 1 - clip) & (adv < 0) | (ratio > 1 + clip) & (adv > 0)
            surr = np.minimum(ratio * adv, np.clip(ratio, 1 - clip, 1 + clip) * adv)
            h = -(p * np.where(mask, lp_all, 0.0)).sum(axis=1)
            dlogp = np.where(clipped, 0.0, -adv * ratio)               # d(-surr)/d logp
            onehot = np.zeros_like(p); onehot[np.arange(m), a] = 1.0
            gz = dlogp[:, None] * (onehot - p)
            gz += ent * p * (np.where(mask, lp_all, 0.0) + h[:, None])  # d(-ent*H)/dz
            gz = gz * mask / m
            _adam(params, "actor", params["actor"], _backward(params["actor"], acts, gz),
                  lr, max_norm)
            cacts = _forward(params["critic"], x)
            v = cacts[-1][:, 0]
            gv = (vf * (v - ret) / m)[:, None]
            _adam(params, "critic", params["critic"], _backward(params["critic"], cacts, gv),
                  lr, max_norm)
            stats["policy_loss"] += float(-surr.mean())
            stats["value_loss"] += float(0.5 * ((v - ret) ** 2).mean())
            stats["entropy"] += float(h.mean())
            stats["clip_frac"] += float(clipped.mean())
            count += 1
    return {k: v / max(count, 1) for k, v in stats.items()}


# ------------------------------------------------------------------- export
def actor_dict(params) -> dict:
    return {"format": FORMAT, "features": int(params["sizes"][0]),
            "sizes": [int(s) for s in params["sizes"]], "activation": "tanh",
            "macros": list(MACRO_SLOTS),
            "layers": [{"w": [[float(v) for v in row] for row in w], "b": [float(v) for v in b]}
                       for w, b in params["actor"]]}


def export_json(params, path) -> str:
    """Write the actor as plain JSON lists; return the file's SHA-256."""
    text = json.dumps(actor_dict(params), sort_keys=True, separators=(",", ":"))
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(text)
    return hashlib.sha256(text.encode()).hexdigest()
