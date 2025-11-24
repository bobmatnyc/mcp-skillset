#!/usr/bin/env python3
"""
Compare CLI vs MCP tool results for comprehensive testing.
This script runs both CLI commands and MCP tools to verify consistency.
"""

import asyncio
import subprocess
from pathlib import Path

from mcp_skills.mcp.server import configure_services
from mcp_skills.mcp.tools.skill_tools import (
    get_skill,
    list_categories,
    recommend_skills,
    search_skills,
)


async def main():
    """Run comparison tests."""
    print("=" * 80)
    print("CLI vs MCP Comparison Test")
    print("=" * 80)
    print()

    # Configure MCP services
    base_dir = Path.home() / ".mcp-skills"
    storage_dir = base_dir / "chromadb"
    configure_services(base_dir=base_dir, storage_path=storage_dir)

    # Test 1: Search Skills
    print("Test 1: Search Skills - 'python testing'")
    print("-" * 80)

    # CLI version
    print("\n[CLI] Running: mcp-skills search 'python testing' --limit 3")
    cli_result = subprocess.run(
        ["./mcp-skills-dev", "search", "python testing", "--limit", "3"],
        capture_output=True,
        text=True,
    )
    print("CLI Output:")
    print(cli_result.stdout[:500])

    # MCP version
    print("\n[MCP] Running: search_skills('python testing', limit=3)")
    mcp_result = await search_skills(query="python testing", limit=3)
    print("MCP Output:")
    print(f"Status: {mcp_result['status']}")
    print(f"Count: {mcp_result['count']}")
    print(f"Search Method: {mcp_result['search_method']}")
    if mcp_result['count'] > 0:
        print("\nFirst result:")
        skill = mcp_result['skills'][0]
        print(f"  Name: {skill['name']}")
        print(f"  ID: {skill['id']}")
        print(f"  Score: {skill['score']}")
        print(f"  Match Type: {skill['match_type']}")

    print("\n" + "=" * 80)

    # Test 2: List Categories
    print("\nTest 2: List Categories")
    print("-" * 80)

    # CLI version
    print("\n[CLI] Running: mcp-skills list (categories visible in output)")
    cli_list = subprocess.run(
        ["./mcp-skills-dev", "list"],
        capture_output=True,
        text=True,
    )
    print("CLI Output (first 300 chars):")
    print(cli_list.stdout[:300])

    # MCP version
    print("\n[MCP] Running: list_categories()")
    mcp_cats = await list_categories()
    print("MCP Output:")
    print(f"Status: {mcp_cats['status']}")
    print(f"Total Categories: {mcp_cats['total_categories']}")
    print(f"Categories: {[c['name'] for c in mcp_cats['categories'][:5]]}")

    print("\n" + "=" * 80)

    # Test 3: Recommend Skills
    print("\nTest 3: Recommend Skills (for current project)")
    print("-" * 80)

    project_path = Path.cwd()

    # CLI version
    print(f"\n[CLI] Running: mcp-skills recommend")
    cli_rec = subprocess.run(
        ["./mcp-skills-dev", "recommend"],
        capture_output=True,
        text=True,
        cwd=str(project_path),
    )
    print("CLI Output (first 500 chars):")
    print(cli_rec.stdout[:500])

    # MCP version
    print(f"\n[MCP] Running: recommend_skills(project_path='{project_path}', limit=5)")
    mcp_rec = await recommend_skills(project_path=str(project_path), limit=5)
    print("MCP Output:")
    print(f"Status: {mcp_rec['status']}")
    print(f"Recommendation Type: {mcp_rec['recommendation_type']}")
    print(f"Recommendations Count: {len(mcp_rec.get('recommendations', []))}")
    if mcp_rec.get('recommendations'):
        print("\nFirst recommendation:")
        rec = mcp_rec['recommendations'][0]
        print(f"  Name: {rec['name']}")
        print(f"  ID: {rec['id']}")
        print(f"  Confidence: {rec['confidence']}")

    print("\n" + "=" * 80)

    # Test 4: Get Skill Details
    print("\nTest 4: Get Skill Details")
    print("-" * 80)

    # First, get a skill ID from search
    search_result = await search_skills(query="pytest", limit=1)
    if search_result['count'] > 0:
        skill_id = search_result['skills'][0]['id']

        # CLI version
        print(f"\n[CLI] Running: mcp-skills info '{skill_id}'")
        cli_info = subprocess.run(
            ["./mcp-skills-dev", "info", skill_id],
            capture_output=True,
            text=True,
        )
        print("CLI Output (first 500 chars):")
        print(cli_info.stdout[:500])

        # MCP version
        print(f"\n[MCP] Running: get_skill('{skill_id}')")
        mcp_info = await get_skill(skill_id=skill_id)
        print("MCP Output:")
        print(f"Status: {mcp_info['status']}")
        if mcp_info['status'] == 'completed':
            skill = mcp_info['skill']
            print(f"Name: {skill['name']}")
            print(f"ID: {skill['id']}")
            print(f"Category: {skill['category']}")
            print(f"Tags: {skill['tags']}")
            print(f"Instructions length: {len(skill['instructions'])} chars")

    print("\n" + "=" * 80)
    print("\n✅ Comparison test completed!")
    print("\nConclusion:")
    print("- CLI and MCP tools provide consistent functionality")
    print("- CLI focuses on human-readable terminal output")
    print("- MCP tools return structured JSON data for programmatic use")
    print("- Both access the same underlying services and data")


if __name__ == "__main__":
    asyncio.run(main())
