#!/usr/bin/env python3
"""Post a comment to a GitHub Discussion via the GraphQL API.

Usage:
    python post_discussion.py --repo owner/name --discussion-number 167 --body "Hello"

Requires GITHUB_TOKEN environment variable with discussions:write permission.
"""

import argparse
import json
import os
import sys
import urllib.request
import urllib.error


GRAPHQL_URL = "https://api.github.com/graphql"


def graphql(token: str, query: str, variables: dict) -> dict:
    """Execute a GitHub GraphQL request."""
    payload = json.dumps({"query": query, "variables": variables}).encode()
    req = urllib.request.Request(
        GRAPHQL_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/vnd.github+json",
        },
    )
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        body = exc.read().decode(errors="replace")
        if exc.code in (401, 403):
            print(
                f"ERROR: GitHub token lacks permission (HTTP {exc.code}). "
                "Ensure the token has 'discussions' write scope.",
                file=sys.stderr,
            )
        else:
            print(f"ERROR: HTTP {exc.code} — {body}", file=sys.stderr)
        sys.exit(1)
    if "errors" in data:
        for err in data["errors"]:
            msg = err.get("message", "")
            if "not authorized" in msg.lower() or "forbidden" in msg.lower():
                print(
                    f"ERROR: GitHub token lacks permission to write to Discussions. "
                    f"Detail: {msg}",
                    file=sys.stderr,
                )
                sys.exit(1)
        print(f"ERROR: GraphQL errors: {data['errors']}", file=sys.stderr)
        sys.exit(1)
    return data


def get_discussion_id(token: str, owner: str, name: str, number: int) -> str:
    """Return the node ID for a discussion given its number."""
    query = """
    query GetDiscussion($owner: String!, $name: String!, $number: Int!) {
      repository(owner: $owner, name: $name) {
        discussion(number: $number) {
          id
        }
      }
    }
    """
    data = graphql(token, query, {"owner": owner, "name": name, "number": number})
    try:
        return data["data"]["repository"]["discussion"]["id"]
    except (KeyError, TypeError):
        print(
            f"ERROR: Discussion #{number} not found in {owner}/{name}.",
            file=sys.stderr,
        )
        sys.exit(1)


def add_comment(token: str, discussion_id: str, body: str) -> str:
    """Add a comment to a discussion and return its URL."""
    mutation = """
    mutation AddComment($discussionId: ID!, $body: String!) {
      addDiscussionComment(input: {discussionId: $discussionId, body: $body}) {
        comment {
          id
          url
        }
      }
    }
    """
    data = graphql(token, mutation, {"discussionId": discussion_id, "body": body})
    try:
        return data["data"]["addDiscussionComment"]["comment"]["url"]
    except (KeyError, TypeError):
        print("ERROR: Unexpected response when adding comment.", file=sys.stderr)
        sys.exit(1)


def post_discussion_comment(
    repo: str,
    discussion_number: int,
    body: str,
    token: str | None = None,
) -> str:
    """Post a comment to a GitHub Discussion. Returns the comment URL."""
    if token is None:
        token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print(
            "ERROR: GITHUB_TOKEN environment variable is not set.",
            file=sys.stderr,
        )
        sys.exit(1)

    parts = repo.split("/")
    if len(parts) != 2:
        print(
            f"ERROR: --repo must be in 'owner/name' format, got: {repo!r}",
            file=sys.stderr,
        )
        sys.exit(1)
    owner, name = parts

    discussion_id = get_discussion_id(token, owner, name, discussion_number)
    url = add_comment(token, discussion_id, body)
    return url


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Post a comment to a GitHub Discussion."
    )
    parser.add_argument(
        "--repo",
        required=True,
        help="Repository in 'owner/name' format",
    )
    parser.add_argument(
        "--discussion-number",
        type=int,
        required=True,
        help="Discussion number to comment on",
    )
    parser.add_argument(
        "--body",
        required=True,
        help="Markdown body of the comment",
    )
    args = parser.parse_args()

    url = post_discussion_comment(
        repo=args.repo,
        discussion_number=args.discussion_number,
        body=args.body,
    )
    print(f"Comment posted: {url}")


if __name__ == "__main__":
    main()
