from typing import Iterable, Iterator, List, Union

import llm
import yaml
from llm import EmbeddingModel, hookimpl
from llm.default_plugins.openai_models import Chat
from openai import AzureOpenAI


@hookimpl
def register_models(register):
    azure_path = config_dir() / "config.yaml"
    with open(azure_path) as f:
        azure_models = yaml.safe_load(f)
    for model in azure_models:
        if not model.get('embedding_model'):
            model_id = model["model_id"]
            model_name = model["deployment_name"]
            endpoint = model["endpoint"]
            api_version = model["api_version"]
            aliases = model.get("aliases", [])
            register(AzureChat(model_id, model_name, endpoint, api_version), aliases=aliases)


@hookimpl
def register_embedding_models(register):
    azure_path = config_dir() / "config.yaml"
    with open(azure_path) as f:
        azure_models = yaml.safe_load(f)
    for model in azure_models:
        if model.get('embedding_model'):
            model_id = model["model_id"]
            model_name = model["deployment_name"]
            endpoint = model["endpoint"]
            api_version = model["api_version"]
            aliases = model.get("aliases", [])
            register(AzureEmbedding(model_id, model_name, endpoint, api_version), aliases=aliases)


class AzureEmbedding(EmbeddingModel):
    needs_key = "azure"
    key_env_var = "AZURE_OPENAI_API_KEY"
    batch_size = 100

    def __init__(self, model_id, model_name, endpoint, api_version):
        self.model_id = model_id
        self.model_name = model_name
        self.endpoint = endpoint
        self.api_version = api_version

    def embed_batch(self, items: Iterable[Union[str, bytes]]) -> Iterator[List[float]]:
        kwargs = {
            "input": items,
            "model": self.model_name,
        }
        client = _get_client(self)
        results = client.embeddings.create(**kwargs).data
        return ([float(r) for r in result.embedding] for result in results)


class AzureChat(Chat):
    needs_key = "azure"
    key_env_var = "AZURE_OPENAI_API_KEY"

    def __init__(self, model_id, model_name, endpoint, api_version):
        self.model_id = model_id
        self.model_name = model_name
        self.endpoint = endpoint
        self.api_version = api_version

    def get_client(self):
        return _get_client(self)


def config_dir():
    dir_path = llm.user_dir() / "azure"
    if not dir_path.exists():
        dir_path.mkdir()
    return dir_path


def _get_client(self):
    return AzureOpenAI(
        api_key=self.key,
        api_version=self.api_version,
        azure_endpoint=self.endpoint,
    )