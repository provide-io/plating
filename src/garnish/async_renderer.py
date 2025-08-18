#
# garnish/async_renderer.py
#
"""Backward compatibility module - redirects to renderer."""

from pathlib import Path

from garnish.renderer import GarnishRenderer, generate_docs as _generate_docs


# Backward compatibility - AsyncGarnishRenderer is now just GarnishRenderer
AsyncGarnishRenderer = GarnishRenderer


# Keep the async signatures for backward compatibility but they're actually sync now
async def generate_docs_async(
    provider_dir: Path = Path(),
    output_dir: str = "docs",
    provider_name: str | None = None,
    **kwargs,
) -> None:
    """Async entry point for documentation generation (actually sync now)."""
    _generate_docs(
        output_dir=output_dir,
        provider_name=provider_name,
        **kwargs
    )


def generate_docs(
    provider_dir: Path = Path(),
    output_dir: str = "docs",
    provider_name: str | None = None,
    **kwargs,
) -> None:
    """Sync entry point for documentation generation."""
    _generate_docs(
        output_dir=output_dir,
        provider_name=provider_name,
        **kwargs
    )


# Backward compatibility adapter
class DocsGenerator:
    """Backward compatibility adapter."""

    def __init__(
        self,
        provider_dir: Path,
        output_dir: str = "docs",
        provider_name: str | None = None,
        **kwargs,
    ):
        self.provider_dir = provider_dir
        self.output_dir = Path(output_dir)
        self.provider_name = provider_name

    def generate(self):
        """Generate documentation."""
        print(f"🔍 Generating documentation...")
        print("📋 Extracting provider schema...")
        print("📁 Processing examples...")
        print("📄 Generating missing templates...")
        print("🎨 Plating templates...")
        
        _generate_docs(
            output_dir=self.output_dir,
            provider_name=self.provider_name,
        )
        
        print(f"✅ Documentation generated successfully in {self.output_dir}")


# 🍲🥄📄🪄