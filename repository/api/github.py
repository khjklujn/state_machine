# standard library imports
from datetime import datetime, UTC
from typing import Any
from urllib.parse import urljoin

# third party imports
import requests
from pydantic import SecretStr

# application imports
from state_machine import AbstractRepository


class GitHub(AbstractRepository):
    """
    Interactions with GitHub API.
    """

    BASE_URL = "https://api.github.com"

    @classmethod
    def execute(
        cls,
        *,
        method: str,
        endpoint: str,
        token: SecretStr | None = None,
        headers: dict[str, str] | None = None,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
    ) -> dict | list[dict]:
        """
        Execute a GitHub API request.

        Args:
            method: HTTP method (GET, POST, PUT, PATCH, DELETE).
            endpoint: API endpoint (e.g., '/repos/owner/repo').
            token: Optional GitHub personal access token for authentication.
            headers: Optional additional headers.
            params: Optional query parameters.
            json: Optional JSON body data.
            data: Optional form data.

        raises:
            Exception: If the API request fails.
        """
        url = urljoin(cls.BASE_URL, endpoint.lstrip("/"))

        request_headers = {"Accept": "application/vnd.github.v3+json"}
        if token:
            request_headers["Authorization"] = f"token {token.get_secret_value()}"
        if headers:
            request_headers.update(headers)

        start_time = datetime.now(UTC)
        cls.logger.debug(f"  GitHub API {method} {url} - Started")

        response = requests.request(
            method=method,
            url=url,
            headers=request_headers,
            params=params,
            json=json,
            data=data,
            timeout=30,
        )

        end_time = datetime.now(UTC)
        cls.logger.debug(
            f"  GitHub API {method} {url} - Completed - Runtime: {end_time - start_time}"
        )

        if not response.ok:
            raise Exception(
                f"GitHub API request failed: {response.status_code} - {response.text}"
            )

        if response.content:
            return response.json()
        return {}

    @classmethod
    def get_user(cls, *, token: SecretStr, username: str | None = None) -> dict:
        """
        Get user information.

        Args:
            token: GitHub personal access token.
            username: Optional username. If not provided, returns authenticated user.

        raises:
            Exception: If the API request fails.
        """
        if username:
            endpoint = f"/users/{username}"
        else:
            endpoint = "/user"

        return cls.execute(method="GET", endpoint=endpoint, token=token)

    @classmethod
    def list_repositories(
        cls,
        *,
        token: SecretStr,
        username: str | None = None,
        type: str | None = None,
        sort: str | None = None,
        direction: str | None = None,
    ) -> list[dict]:
        """
        List repositories.

        Args:
            token: GitHub personal access token.
            username: Optional username. If not provided, lists repositories for authenticated user.
            type: Optional filter by repository type (all, owner, member).
            sort: Optional sort field (created, updated, pushed, full_name).
            direction: Optional sort direction (asc, desc).

        raises:
            Exception: If the API request fails.
        """
        if username:
            endpoint = f"/users/{username}/repos"
        else:
            endpoint = "/user/repos"

        params = {}
        if type:
            params["type"] = type
        if sort:
            params["sort"] = sort
        if direction:
            params["direction"] = direction

        return cls.execute(method="GET", endpoint=endpoint, token=token, params=params)

    @classmethod
    def get_repository(cls, *, token: SecretStr, owner: str, repo: str) -> dict:
        """
        Get repository information.

        Args:
            token: GitHub personal access token.
            owner: Repository owner username or organization.
            repo: Repository name.

        raises:
            Exception: If the API request fails.
        """
        endpoint = f"/repos/{owner}/{repo}"

        return cls.execute(method="GET", endpoint=endpoint, token=token)

    @classmethod
    def create_repository(
        cls,
        *,
        token: SecretStr,
        name: str,
        description: str | None = None,
        private: bool = False,
        has_issues: bool = True,
        has_projects: bool = True,
        has_wiki: bool = True,
        auto_init: bool = False,
    ) -> dict:
        """
        Create a new repository.

        Args:
            token: GitHub personal access token.
            name: Repository name.
            description: Optional repository description.
            private: Whether the repository should be private.
            has_issues: Enable issues for the repository.
            has_projects: Enable projects for the repository.
            has_wiki: Enable wiki for the repository.
            auto_init: Create an initial commit with empty README.

        raises:
            Exception: If the API request fails.
        """
        endpoint = "/user/repos"

        json_data = {
            "name": name,
            "private": private,
            "has_issues": has_issues,
            "has_projects": has_projects,
            "has_wiki": has_wiki,
            "auto_init": auto_init,
        }
        if description:
            json_data["description"] = description

        return cls.execute(method="POST", endpoint=endpoint, token=token, json=json_data)

    @classmethod
    def update_repository(
        cls,
        *,
        token: SecretStr,
        owner: str,
        repo: str,
        name: str | None = None,
        description: str | None = None,
        private: bool | None = None,
        has_issues: bool | None = None,
        has_projects: bool | None = None,
        has_wiki: bool | None = None,
    ) -> dict:
        """
        Update repository information.

        Args:
            token: GitHub personal access token.
            owner: Repository owner username or organization.
            repo: Repository name.
            name: Optional new repository name.
            description: Optional new repository description.
            private: Optional visibility setting.
            has_issues: Optional enable/disable issues.
            has_projects: Optional enable/disable projects.
            has_wiki: Optional enable/disable wiki.

        raises:
            Exception: If the API request fails.
        """
        endpoint = f"/repos/{owner}/{repo}"

        json_data = {}
        if name is not None:
            json_data["name"] = name
        if description is not None:
            json_data["description"] = description
        if private is not None:
            json_data["private"] = private
        if has_issues is not None:
            json_data["has_issues"] = has_issues
        if has_projects is not None:
            json_data["has_projects"] = has_projects
        if has_wiki is not None:
            json_data["has_wiki"] = has_wiki

        return cls.execute(method="PATCH", endpoint=endpoint, token=token, json=json_data)

    @classmethod
    def delete_repository(cls, *, token: SecretStr, owner: str, repo: str) -> None:
        """
        Delete a repository.

        Args:
            token: GitHub personal access token.
            owner: Repository owner username or organization.
            repo: Repository name.

        raises:
            Exception: If the API request fails.
        """
        endpoint = f"/repos/{owner}/{repo}"

        cls.execute(method="DELETE", endpoint=endpoint, token=token)

    @classmethod
    def list_issues(
        cls,
        *,
        token: SecretStr,
        owner: str,
        repo: str,
        state: str | None = None,
        labels: str | None = None,
        sort: str | None = None,
        direction: str | None = None,
        since: str | None = None,
    ) -> list[dict]:
        """
        List issues for a repository.

        Args:
            token: GitHub personal access token.
            owner: Repository owner username or organization.
            repo: Repository name.
            state: Optional issue state filter (open, closed, all).
            labels: Optional comma-separated list of label names.
            sort: Optional sort field (created, updated, comments).
            direction: Optional sort direction (asc, desc).
            since: Optional ISO 8601 timestamp to filter issues updated after.

        raises:
            Exception: If the API request fails.
        """
        endpoint = f"/repos/{owner}/{repo}/issues"

        params = {}
        if state:
            params["state"] = state
        if labels:
            params["labels"] = labels
        if sort:
            params["sort"] = sort
        if direction:
            params["direction"] = direction
        if since:
            params["since"] = since

        return cls.execute(method="GET", endpoint=endpoint, token=token, params=params)

    @classmethod
    def create_issue(
        cls,
        *,
        token: SecretStr,
        owner: str,
        repo: str,
        title: str,
        body: str | None = None,
        labels: list[str] | None = None,
        assignees: list[str] | None = None,
    ) -> dict:
        """
        Create an issue.

        Args:
            token: GitHub personal access token.
            owner: Repository owner username or organization.
            repo: Repository name.
            title: Issue title.
            body: Optional issue body text.
            labels: Optional list of label names.
            assignees: Optional list of usernames to assign.

        raises:
            Exception: If the API request fails.
        """
        endpoint = f"/repos/{owner}/{repo}/issues"

        json_data = {"title": title}
        if body:
            json_data["body"] = body
        if labels:
            json_data["labels"] = labels
        if assignees:
            json_data["assignees"] = assignees

        return cls.execute(method="POST", endpoint=endpoint, token=token, json=json_data)

    @classmethod
    def list_pull_requests(
        cls,
        *,
        token: SecretStr,
        owner: str,
        repo: str,
        state: str | None = None,
        head: str | None = None,
        base: str | None = None,
        sort: str | None = None,
        direction: str | None = None,
    ) -> list[dict]:
        """
        List pull requests for a repository.

        Args:
            token: GitHub personal access token.
            owner: Repository owner username or organization.
            repo: Repository name.
            state: Optional PR state filter (open, closed, all).
            head: Optional filter by head branch or user.
            base: Optional filter by base branch.
            sort: Optional sort field (created, updated, popularity).
            direction: Optional sort direction (asc, desc).

        raises:
            Exception: If the API request fails.
        """
        endpoint = f"/repos/{owner}/{repo}/pulls"

        params = {}
        if state:
            params["state"] = state
        if head:
            params["head"] = head
        if base:
            params["base"] = base
        if sort:
            params["sort"] = sort
        if direction:
            params["direction"] = direction

        return cls.execute(method="GET", endpoint=endpoint, token=token, params=params)

    @classmethod
    def create_pull_request(
        cls,
        *,
        token: SecretStr,
        owner: str,
        repo: str,
        title: str,
        head: str,
        base: str,
        body: str | None = None,
        draft: bool = False,
    ) -> dict:
        """
        Create a pull request.

        Args:
            token: GitHub personal access token.
            owner: Repository owner username or organization.
            repo: Repository name.
            title: Pull request title.
            head: The branch that contains changes.
            base: The branch to merge changes into.
            body: Optional pull request body text.
            draft: Whether to create as a draft PR.

        raises:
            Exception: If the API request fails.
        """
        endpoint = f"/repos/{owner}/{repo}/pulls"

        json_data = {
            "title": title,
            "head": head,
            "base": base,
            "draft": draft,
        }
        if body:
            json_data["body"] = body

        return cls.execute(method="POST", endpoint=endpoint, token=token, json=json_data)

    @classmethod
    def list_releases(
        cls,
        *,
        token: SecretStr,
        owner: str,
        repo: str,
        per_page: int | None = None,
        page: int | None = None,
    ) -> list[dict]:
        """
        List releases for a repository.

        Args:
            token: GitHub personal access token.
            owner: Repository owner username or organization.
            repo: Repository name.
            per_page: Optional number of results per page (max 100).
            page: Optional page number.

        raises:
            Exception: If the API request fails.
        """
        endpoint = f"/repos/{owner}/{repo}/releases"

        params = {}
        if per_page:
            params["per_page"] = per_page
        if page:
            params["page"] = page

        return cls.execute(method="GET", endpoint=endpoint, token=token, params=params)

    @classmethod
    def create_release(
        cls,
        *,
        token: SecretStr,
        owner: str,
        repo: str,
        tag_name: str,
        target_commitish: str | None = None,
        name: str | None = None,
        body: str | None = None,
        draft: bool = False,
        prerelease: bool = False,
    ) -> dict:
        """
        Create a release.

        Args:
            token: GitHub personal access token.
            owner: Repository owner username or organization.
            repo: Repository name.
            tag_name: The name of the tag.
            target_commitish: Optional target commit/branch.
            name: Optional release name.
            body: Optional release notes.
            draft: Whether to create as a draft release.
            prerelease: Whether to mark as a prerelease.

        raises:
            Exception: If the API request fails.
        """
        endpoint = f"/repos/{owner}/{repo}/releases"

        json_data = {
            "tag_name": tag_name,
            "draft": draft,
            "prerelease": prerelease,
        }
        if target_commitish:
            json_data["target_commitish"] = target_commitish
        if name:
            json_data["name"] = name
        if body:
            json_data["body"] = body

        return cls.execute(method="POST", endpoint=endpoint, token=token, json=json_data)

    @classmethod
    def list_branches(
        cls,
        *,
        token: SecretStr,
        owner: str,
        repo: str,
        protected: bool | None = None,
    ) -> list[dict]:
        """
        List branches for a repository.

        Args:
            token: GitHub personal access token.
            owner: Repository owner username or organization.
            repo: Repository name.
            protected: Optional filter by protected status.

        raises:
            Exception: If the API request fails.
        """
        endpoint = f"/repos/{owner}/{repo}/branches"

        params = {}
        if protected is not None:
            params["protected"] = protected

        return cls.execute(method="GET", endpoint=endpoint, token=token, params=params)

    @classmethod
    def get_branch(cls, *, token: SecretStr, owner: str, repo: str, branch: str) -> dict:
        """
        Get branch information.

        Args:
            token: GitHub personal access token.
            owner: Repository owner username or organization.
            repo: Repository name.
            branch: Branch name.

        raises:
            Exception: If the API request fails.
        """
        endpoint = f"/repos/{owner}/{repo}/branches/{branch}"

        return cls.execute(method="GET", endpoint=endpoint, token=token)

    @classmethod
    def list_commits(
        cls,
        *,
        token: SecretStr,
        owner: str,
        repo: str,
        sha: str | None = None,
        path: str | None = None,
        author: str | None = None,
        since: str | None = None,
        until: str | None = None,
    ) -> list[dict]:
        """
        List commits for a repository.

        Args:
            token: GitHub personal access token.
            owner: Repository owner username or organization.
            repo: Repository name.
            sha: Optional SHA or branch to start listing commits from.
            path: Optional path to filter commits by.
            author: Optional author username to filter commits.
            since: Optional ISO 8601 timestamp to filter commits after.
            until: Optional ISO 8601 timestamp to filter commits before.

        raises:
            Exception: If the API request fails.
        """
        endpoint = f"/repos/{owner}/{repo}/commits"

        params = {}
        if sha:
            params["sha"] = sha
        if path:
            params["path"] = path
        if author:
            params["author"] = author
        if since:
            params["since"] = since
        if until:
            params["until"] = until

        return cls.execute(method="GET", endpoint=endpoint, token=token, params=params)

    @classmethod
    def get_commit(cls, *, token: SecretStr, owner: str, repo: str, sha: str) -> dict:
        """
        Get commit information.

        Args:
            token: GitHub personal access token.
            owner: Repository owner username or organization.
            repo: Repository name.
            sha: Commit SHA.

        raises:
            Exception: If the API request fails.
        """
        endpoint = f"/repos/{owner}/{repo}/commits/{sha}"

        return cls.execute(method="GET", endpoint=endpoint, token=token)
