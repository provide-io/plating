# Create a bundle for a resource component
locals {
  bundle_config = {
    name          = "s3_bucket"
    garnish_dir   = "./resources/s3_bucket.garnish"
    component_type = "resource"
  }
}

# Python equivalent:
# from pathlib import Path
# from garnish.garnish import GarnishBundle
#
# bundle = GarnishBundle(
#     name="s3_bucket",
#     garnish_dir=Path("./resources/s3_bucket.garnish"),
#     component_type="resource"
# )