"""
Proof Generator — Merkle Tree Hashing & Compact Proof for Acoustic Link

Builds a Merkle tree from sensor log entries, produces a SHA-256 root hash,
and simulates transmission over a low-bandwidth acoustic modem.

The "Store-and-Forward" protocol:
    1. Every 10 minutes: build Merkle tree → send 32-byte root via acoustic link
    2. On surfacing: dump full dataset via optical link for verification
    3. On-chain: compare committed root against full-data root to verify integrity
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from dataclasses import dataclass, field

logger = logging.getLogger("guardian_oracle.proof_generator")


@dataclass
class CompactProof:
    """A minimised proof suitable for acoustic transmission."""
    merkle_root: str            # SHA-256 hex digest (64 chars)
    leaf_count: int             # Number of log entries in the tree
    timestamp: float            # When the proof was generated
    transmission_bytes: int     # Size of the acoustic payload

    def __repr__(self) -> str:
        return (
            f"CompactProof(root={self.merkle_root[:16]}..., "
            f"leaves={self.leaf_count}, "
            f"tx_bytes={self.transmission_bytes})"
        )


class MerkleTree:
    """
    A simple binary Merkle tree built from SHA-256 leaf hashes.
    
    Each leaf is the SHA-256 hash of a JSON-serialized sensor log entry.
    Internal nodes are the SHA-256 hash of their two children concatenated.
    """

    def __init__(self, leaves: list[str]):
        """
        Args:
            leaves: List of hex-encoded SHA-256 leaf hashes.
        """
        if not leaves:
            raise ValueError("Cannot build Merkle tree with zero leaves")

        self._leaves = leaves
        self._root = self._build(leaves)

    @staticmethod
    def hash_data(data: str) -> str:
        """SHA-256 hash of a string, returned as hex."""
        return hashlib.sha256(data.encode("utf-8")).hexdigest()

    @staticmethod
    def hash_pair(left: str, right: str) -> str:
        """SHA-256 hash of two hex hashes concatenated."""
        combined = left + right
        return hashlib.sha256(combined.encode("utf-8")).hexdigest()

    def _build(self, nodes: list[str]) -> str:
        """Recursively build the tree, returning the root hash."""
        if len(nodes) == 1:
            return nodes[0]

        # If odd number of nodes, duplicate the last
        if len(nodes) % 2 == 1:
            nodes = nodes + [nodes[-1]]

        # Pairwise hash
        parent_level = []
        for i in range(0, len(nodes), 2):
            parent_level.append(self.hash_pair(nodes[i], nodes[i + 1]))

        return self._build(parent_level)

    @property
    def root(self) -> str:
        return self._root

    @property
    def leaf_count(self) -> int:
        return len(self._leaves)


class ProofGenerator:
    """
    Manages Merkle tree construction and acoustic transmission simulation.
    """

    # Acoustic modem specs (simulated)
    ACOUSTIC_BANDWIDTH_BPS = 100    # ~100 bits per second
    HASH_SIZE_BYTES = 32            # SHA-256 = 32 bytes
    HEADER_BYTES = 8                # Protocol overhead (timestamp + leaf count)

    def __init__(self):
        self._proof_count = 0
        self._proofs: list[CompactProof] = []

    @property
    def proof_count(self) -> int:
        return self._proof_count

    @property
    def proofs(self) -> list[CompactProof]:
        return list(self._proofs)

    def build_merkle_tree(self, log_entries: list[dict]) -> MerkleTree:
        """
        Build a Merkle tree from a list of sensor log dictionaries.
        
        Each entry is JSON-serialized and SHA-256 hashed to form a leaf.
        
        Args:
            log_entries: List of sensor log dictionaries.
        
        Returns:
            MerkleTree with computed root hash.
        """
        if not log_entries:
            raise ValueError("Cannot build proof from empty log")

        leaves = []
        for entry in log_entries:
            serialized = json.dumps(entry, sort_keys=True, default=str)
            leaf_hash = MerkleTree.hash_data(serialized)
            leaves.append(leaf_hash)

        return MerkleTree(leaves)

    def generate_compact_proof(self, tree: MerkleTree) -> CompactProof:
        """
        Generate a compact proof from a Merkle tree for acoustic transmission.
        
        The proof contains only:
            - 32-byte Merkle root hash
            - 4-byte leaf count
            - 4-byte timestamp
        Total: 40 bytes — transmittable in ~3.2 seconds at 100 bps.
        """
        tx_bytes = self.HASH_SIZE_BYTES + self.HEADER_BYTES

        proof = CompactProof(
            merkle_root=tree.root,
            leaf_count=tree.leaf_count,
            timestamp=time.time(),
            transmission_bytes=tx_bytes,
        )

        self._proof_count += 1
        self._proofs.append(proof)

        return proof

    def simulate_acoustic_send(self, proof: CompactProof) -> dict:
        """
        Simulate sending the compact proof via an acoustic modem.
        
        Returns:
            dict with transmission metadata.
        """
        tx_time_seconds = (proof.transmission_bytes * 8) / self.ACOUSTIC_BANDWIDTH_BPS

        result = {
            "status": "SENT",
            "merkle_root": proof.merkle_root,
            "leaf_count": proof.leaf_count,
            "transmission_bytes": proof.transmission_bytes,
            "estimated_tx_time_seconds": round(tx_time_seconds, 2),
            "bandwidth_bps": self.ACOUSTIC_BANDWIDTH_BPS,
            "timestamp": proof.timestamp,
        }

        logger.info(
            f"ACOUSTIC TX: {proof.transmission_bytes} bytes, "
            f"{tx_time_seconds:.1f}s at {self.ACOUSTIC_BANDWIDTH_BPS} bps | "
            f"Root: {proof.merkle_root[:16]}..."
        )

        return result

    def build_and_send(self, log_entries: list[dict]) -> dict:
        """
        Convenience method: build tree → generate proof → simulate send.
        
        Returns:
            dict with transmission result including merkle_root.
        """
        tree = self.build_merkle_tree(log_entries)
        proof = self.generate_compact_proof(tree)
        result = self.simulate_acoustic_send(proof)
        return result
