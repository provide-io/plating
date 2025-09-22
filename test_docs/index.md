---
page_title: "Default Provider"
description: |-
  Terraform provider for default
---

# Default Provider

Terraform provider for default - A Python-based Terraform provider built with the Pyvider framework.

## Example Usage

```terraform
provider "default" {
  # Configuration options
}
```

## Schema

No provider configuration required.

## Resources

- [`default_file_content`](./resource/file_content.md)
- [`default_local_directory`](./resource/local_directory.md)
- [`default_private_state_verifier`](./resource/private_state_verifier.md)
- [`default_timed_token`](./resource/timed_token.md)
- [`default_warning_example`](./resource/warning_example.md)

## Data Sources

- [`default_env_variables`](./data_source/env_variables.md)
- [`default_file_info`](./data_source/file_info.md)
- [`default_http_api`](./data_source/http_api.md)
- [`default_lens_jq`](./data_source/lens_jq.md)
- [`default_nested_data_test_suite`](./data_source/nested_data_test_suite.md)
- [`default_provider_config_reader`](./data_source/provider_config_reader.md)

## Functions

- [`add`](./function/add.md)
- [`contains`](./function/contains.md)
- [`divide`](./function/divide.md)
- [`format`](./function/format.md)
- [`join`](./function/join.md)
- [`length`](./function/length.md)
- [`lens_jq`](./function/lens_jq.md)
- [`lookup`](./function/lookup.md)
- [`lower`](./function/lower.md)
- [`max`](./function/max.md)
- [`min`](./function/min.md)
- [`multiply`](./function/multiply.md)
- [`replace`](./function/replace.md)
- [`round`](./function/round.md)
- [`split`](./function/split.md)
- [`subtract`](./function/subtract.md)
- [`sum`](./function/sum.md)
- [`tostring`](./function/tostring.md)
- [`upper`](./function/upper.md)
