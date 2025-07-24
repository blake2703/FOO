"""
cls_blockchain.py
Blockchain Integrity System for Multi-Agent Chat
Ensures conversation logs cannot be tampered with without detection.

By Juan B. Gutiérrez, Professor of Mathematics 
University of Texas at San Antonio.

License: Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)
"""

import hashlib
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple


class ConversationBlockchain:
    """
    Implements blockchain-style integrity checking for conversation logs.
    Each message becomes a block in the chain with cryptographic verification.
    """
    
    def __init__(self, agent_name: str, salt: Optional[str] = None, global_salt: Optional[str] = None, genesis_hash: Optional[str] = None):
        self.agent_name = agent_name
        # Use global salt if provided, otherwise use provided salt, otherwise generate new
        if global_salt:
            self.salt = global_salt
        elif salt:
            self.salt = salt
        else:
            self.salt = self._generate_salt()
        
        # Use provided genesis hash if available, otherwise create new one
        if genesis_hash:
            self.genesis_hash = genesis_hash
        else:
            self.genesis_hash = self._create_genesis_hash()
    
    def _generate_salt(self) -> str:
        """Generate a unique salt for this agent's blockchain"""
        timestamp = str(time.time())
        content = f"{self.agent_name}_{timestamp}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def _create_genesis_hash(self) -> str:
        """Create the genesis block hash"""
        genesis_data = {
            "agent": self.agent_name,
            "genesis": True,
            "salt": self.salt,
            "timestamp": "2025-07-19T00:00:00.000000"  # Fixed timestamp for consistent genesis
        }
        return self._compute_hash(json.dumps(genesis_data, sort_keys=True))
    
    def _compute_hash(self, data: str) -> str:
        """Compute SHA-256 hash of data"""
        return hashlib.sha256((data + self.salt).encode()).hexdigest()
    
    def _create_message_hash(self, role: str, content: str, timestamp: str, 
                           previous_hash: str) -> str:
        """Create hash for a message block - excludes agent name for flexibility"""
        message_data = {
            "role": role,
            "content": content,
            "timestamp": timestamp,
            "previous_hash": previous_hash
        }
        return self._compute_hash(json.dumps(message_data, sort_keys=True))
    
    def add_message_to_chain(self, role: str, content: str, 
                           timestamp: str, history: List[Dict]) -> Dict:
        """
        Add a new message to the blockchain and return the complete entry
        """
        # Get previous hash
        if not history:
            previous_hash = self.genesis_hash
        else:
            previous_hash = history[-1].get("blockchain", {}).get("current_hash", self.genesis_hash)
        
        # Create current hash
        current_hash = self._create_message_hash(role, content, timestamp, previous_hash)
        
        # Create the complete message entry
        message_entry = {
            "role": role,
            "content": content,
            "timestamp": timestamp,
            "hash": self._compute_hash(f"{role}_{content}_{timestamp}"),  # Content-only hash
            "blockchain": {
                "current_hash": current_hash,
                "previous_hash": previous_hash,
                "block_index": len(history),
                "integrity_verified": True
            }
        }
        
        return message_entry
    
    def verify_chain_integrity(self, history: List[Dict]) -> Tuple[bool, List[str]]:
        """
        Verify the entire blockchain integrity
        Returns (is_valid, list_of_errors)
        """
        if not history:
            return True, []
        
        errors = []
        previous_hash = self.genesis_hash
        
        for i, entry in enumerate(history):
            # Check if entry has blockchain data
            if "blockchain" not in entry:
                errors.append(f"Block {i}: Missing blockchain data")
                continue
            
            blockchain_data = entry["blockchain"]
            stored_hash = blockchain_data.get("current_hash")
            stored_previous = blockchain_data.get("previous_hash")
            
            # Verify previous hash chain
            if stored_previous != previous_hash:
                errors.append(f"Block {i}: Previous hash mismatch. Expected: {previous_hash[:16]}..., Got: {stored_previous[:16] if stored_previous else 'None'}...")
            
            # Verify current hash
            calculated_hash = self._create_message_hash(
                entry["role"], 
                entry["content"], 
                entry["timestamp"], 
                stored_previous
            )
            
            if stored_hash != calculated_hash:
                errors.append(f"Block {i}: Hash verification failed. Content may have been tampered with.")
            
            # Verify simple content hash if present
            if "hash" in entry:
                expected_content_hash = self._compute_hash(f"{entry['role']}_{entry['content']}_{entry['timestamp']}")
                if entry["hash"] != expected_content_hash:
                    errors.append(f"Block {i}: Content hash mismatch. Message content may have been altered.")
            
            previous_hash = stored_hash
        
        return len(errors) == 0, errors
    
    def rebuild_chain_from_index(self, history: List[Dict], start_index: int) -> List[Dict]:
        """
        Rebuild the blockchain from a specific index onward.
        Used when user legitimately edits history.
        """
        if start_index == 0:
            previous_hash = self.genesis_hash
        else:
            previous_hash = history[start_index - 1]["blockchain"]["current_hash"]
        
        rebuilt_history = history[:start_index].copy()
        
        for i in range(start_index, len(history)):
            entry = history[i]
            # Rebuild this block
            new_entry = self.add_message_to_chain(
                entry["role"],
                entry["content"], 
                entry["timestamp"],
                rebuilt_history
            )
            rebuilt_history.append(new_entry)
        
        return rebuilt_history
    
    def get_chain_metadata(self, history: List[Dict]) -> Dict:
        """Get metadata about the blockchain"""
        if not history:
            return {
                "total_blocks": 0,
                "genesis_hash": self.genesis_hash,
                "last_hash": self.genesis_hash,
                "agent": self.agent_name,
                "salt": self.salt
            }
        
        return {
            "total_blocks": len(history),
            "genesis_hash": self.genesis_hash,
            "last_hash": history[-1]["blockchain"]["current_hash"],
            "agent": self.agent_name,
            "salt": self.salt,
            "integrity_verified": self.verify_chain_integrity(history)[0]
        }


class IntegrityManager:
    """
    Manages blockchain integrity across all agents in the multi-agent system.
    Integrates with the existing cls_foo.py architecture.
    """
    
    def __init__(self, global_salt: Optional[str] = None):
        self.blockchains: Dict[str, ConversationBlockchain] = {}
        self.global_salt = global_salt
    
    def get_or_create_blockchain(self, agent_name: str, 
                                existing_metadata: Optional[Dict] = None) -> ConversationBlockchain:
        """Get existing blockchain or create new one for agent"""
        if agent_name not in self.blockchains:
            salt = None
            genesis_hash = None
            if existing_metadata:
                salt = existing_metadata.get("salt")
                genesis_hash = existing_metadata.get("genesis_hash")
            
            self.blockchains[agent_name] = ConversationBlockchain(
                agent_name, 
                salt=salt,
                global_salt=self.global_salt,
                genesis_hash=genesis_hash
            )
        
        return self.blockchains[agent_name]
    
    def add_message_with_integrity(self, agent_name: str, role: str, 
                                 content: str, timestamp: str, 
                                 history: List[Dict]) -> Dict:
        """Add a message with blockchain integrity"""
        blockchain = self.get_or_create_blockchain(agent_name)
        return blockchain.add_message_to_chain(role, content, timestamp, history)
    
    def verify_agent_integrity(self, agent_name: str, 
                             history: List[Dict]) -> Tuple[bool, List[str]]:
        """Verify integrity for a specific agent"""
        blockchain = self.get_or_create_blockchain(agent_name)
        return blockchain.verify_chain_integrity(history)
    
    def rebuild_agent_chain(self, agent_name: str, history: List[Dict], 
                          start_index: int) -> List[Dict]:
        """Rebuild chain for agent from specific index"""
        blockchain = self.get_or_create_blockchain(agent_name)
        return blockchain.rebuild_chain_from_index(history, start_index)
    
    def get_integrity_report(self, agent_name: str, 
                           history: List[Dict]) -> Dict:
        """Get comprehensive integrity report for an agent"""
        blockchain = self.get_or_create_blockchain(agent_name)
        is_valid, errors = blockchain.verify_chain_integrity(history)
        metadata = blockchain.get_chain_metadata(history)
        
        return {
            "agent": agent_name,
            "integrity_valid": is_valid,
            "errors": errors,
            "metadata": metadata,
            "verification_timestamp": datetime.now().isoformat()
        }
    
    def migrate_existing_history(self, agent_name: str, 
                               history: List[Dict]) -> List[Dict]:
        """
        Migrate existing history without blockchain data to include integrity checking.
        This is for backward compatibility with existing conversation files.
        """
        blockchain = self.get_or_create_blockchain(agent_name)
        migrated_history = []
        
        for entry in history:
            if "blockchain" not in entry:
                # Add blockchain data to existing entry
                new_entry = blockchain.add_message_to_chain(
                    entry["role"],
                    entry["content"],
                    entry.get("timestamp", datetime.now().isoformat()),
                    migrated_history
                )
                migrated_history.append(new_entry)
            else:
                # Entry already has blockchain data
                migrated_history.append(entry)
        
        return migrated_history


# Example usage and testing
if __name__ == "__main__":
    # Test the blockchain integrity system
    integrity_manager = IntegrityManager()
    
    # Simulate adding messages
    history = []
    
    # Add first message
    message1 = integrity_manager.add_message_with_integrity(
        "TestAgent", "user", "Hello", "2025-07-19T10:00:00", history
    )
    history.append(message1)
    print("Added message 1:", json.dumps(message1, indent=2))
    
    # Add second message
    message2 = integrity_manager.add_message_with_integrity(
        "TestAgent", "assistant", "Hello! How can I help?", "2025-07-19T10:00:01", history
    )
    history.append(message2)
    
    # Verify integrity
    is_valid, errors = integrity_manager.verify_agent_integrity("TestAgent", history)
    print(f"\nIntegrity check: {is_valid}")
    if errors:
        print("Errors:", errors)
    
    # Simulate tampering
    print("\n--- Simulating tampering ---")
    history[0]["content"] = "Hello TAMPERED"
    
    is_valid, errors = integrity_manager.verify_agent_integrity("TestAgent", history)
    print(f"Integrity check after tampering: {is_valid}")
    print("Errors:", errors)
    
    # Get integrity report
    report = integrity_manager.get_integrity_report("TestAgent", history)
    print("\nIntegrity Report:", json.dumps(report, indent=2))