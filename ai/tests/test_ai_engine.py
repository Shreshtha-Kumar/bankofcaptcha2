import os
import sys
import unittest
import torch

# Add ai directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from inference import (
    load_action_registry,
    load_ai_config,
    InsiderThreatLSTM,
    ACTION_MAP,
    VOCAB_SIZE,
    ROLE_PERMISSIONS,
    ROLE_ID_MAP,
    NUM_ROLES
)

class TestAiEngine(unittest.TestCase):

    def test_action_registry_loading(self):
        """Verify that the action registry is properly parsed and role mappings exist."""
        self.assertGreater(VOCAB_SIZE, 0)
        self.assertGreaterEqual(NUM_ROLES, 6)
        self.assertIn("ROLE_CUSTOMER", ROLE_ID_MAP)
        self.assertIn("ROLE_TELLER", ROLE_ID_MAP)
        self.assertIn("ROLE_SUPER_ADMIN", ROLE_ID_MAP)
        self.assertGreater(len(ROLE_PERMISSIONS), 0)
        self.assertGreater(len(ACTION_MAP), 0)

    def test_ai_config_loading(self):
        """Verify that AI configuration parameters are present."""
        config = load_ai_config()
        self.assertIn("lstm", config)
        self.assertIn("signal_weights", config)
        self.assertIn("alerting", config)
        self.assertGreater(config["lstm"]["embedding_dim"], 0)
        self.assertGreater(config["lstm"]["hidden_dim"], 0)

    def test_lstm_model_forward_pass(self):
        """Verify the role-conditioned LSTM Autoencoder model initialization and forward pass tensor shape."""
        seq_len = 10
        embed_dim = 16
        hidden_dim = 32
        batch_size = 2

        model = InsiderThreatLSTM(
            seq_len=seq_len,
            vocab_size=VOCAB_SIZE,
            num_roles=NUM_ROLES,
            embedding_dim=embed_dim,
            hidden_dim=hidden_dim,
            num_layers=1
        )
        model.eval()

        dummy_actions = torch.randint(0, VOCAB_SIZE, (batch_size, seq_len))
        dummy_roles = torch.tensor([ROLE_ID_MAP["ROLE_CUSTOMER"], ROLE_ID_MAP["ROLE_TELLER"]])

        with torch.no_grad():
            reconstructed, target_emb = model(dummy_actions, dummy_roles)

        self.assertEqual(reconstructed.shape, (batch_size, seq_len, embed_dim))
        self.assertEqual(target_emb.shape, (batch_size, seq_len, embed_dim))
        self.assertFalse(torch.isnan(reconstructed).any())

if __name__ == "__main__":
    unittest.main()
