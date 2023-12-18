import sys

import torch
from omegaconf import DictConfig
from omegaconf import OmegaConf as om
from rich.pretty import pprint
import time
from omnivault.transformer.config.composer import Composer, DataConfig
from omnivault.transformer.config.optimizer import AdamConfig, OptimizerConfig
from omnivault.transformer.config.decoder import DecoderConfig, DecoderBlockConfig, MultiHeadedAttentionConfig, PositionwiseFeedForwardConfig, AddNormConfig
from omnivault.transformer.utils.reproducibility import seed_all
from hydra.utils import instantiate
# TODO: I have a callable instead of _target_ field for me to use importlib to parse.
# so maybe consider using my own code base?

seed_all(42)

OPTIMIZER_REGISTRY = {
    "torch.optim.Adam": AdamConfig,
}

if __name__ == "__main__":
    # python omnivault/transformer/main.py omnivault/transformer/config.yaml data.train_loader.batch_size=22
    yaml_path, args_list = sys.argv[1], sys.argv[2:]
    with open(yaml_path) as f:
        yaml_cfg = om.load(f)
    cli_cfg = om.from_cli(args_list)
    cfg = om.merge(yaml_cfg, cli_cfg)
    om.resolve(cfg)
    pprint(cfg)
    assert isinstance(cfg, DictConfig)

    data_config = DataConfig(**cfg.data)
    pprint(data_config)

    optimizer_config = OptimizerConfig(**cfg.optimizer)
    pprint(optimizer_config)
    optimizer_name = optimizer_config.name
    optimizer_config_cls = OPTIMIZER_REGISTRY[optimizer_name]
    optimizer_pydantic_config = optimizer_config_cls(**cfg.optimizer)
    pprint(optimizer_pydantic_config)

    # Define a model with a non-linear activation function
    model = torch.nn.Sequential(torch.nn.Linear(2, 4), torch.nn.ReLU(), torch.nn.Linear(4, 2))
    optimizer = optimizer_pydantic_config.build(params=model.parameters())
    pprint(optimizer)
    # train

    feed_forward_config = instantiate(cfg.feed_forward)
    pprint(feed_forward_config)
    pprint(type(feed_forward_config.activation))
    pprint(type(feed_forward_config))

    feed_forward_config = PositionwiseFeedForwardConfig(**feed_forward_config)
    pprint(feed_forward_config)
    #feed_forward_config.activation = instantiate(feed_forward_config.activation)
    #pprint(feed_forward_config)

    #attention_config =
    attention = instantiate(cfg.attention)
    pprint(attention)

    composer = Composer(data=data_config, optimizer=optimizer_pydantic_config)
    pprint(composer)

    # # Define a simple dataset
    # inputs = torch.randn(100, 2)
    # targets = torch.randn(100, 2)  # Targets should have some relationship to inputs

    # # Train the model
    # for epoch in range(100):
    #     optimizer.zero_grad()
    #     output = model(inputs)
    #     loss = torch.nn.functional.mse_loss(output, targets)
    #     loss.backward()
    #     optimizer.step()
    #     print(f"Epoch {epoch} loss: {loss}")

    # main(cfg)
