"""Tests that Collections can be uploaded to  Pulp with the ansible-galaxy CLI."""

import random
import string
import subprocess
import tempfile
import os

from pulp_smash.pulp3.bindings import delete_orphans
from pulp_smash.pulp3.utils import gen_repo
from pulp_smash.utils import http_get, uuid4

from pulp_ansible.tests.functional.utils import wait_tasks


def test_upload_collection(
    ansible_repo_api_client,
    ansible_repo_version_api_client,
    ansible_distribution_factory,
    create_ansible_cfg,
    gen_object_with_cleanup,
    pulp_admin_user,
):
    with pulp_admin_user:
        repo = gen_object_with_cleanup(ansible_repo_api_client, gen_repo())

        # Create a distribution.
        distribution = ansible_distribution_factory(repo)

        with tempfile.TemporaryDirectory() as temp_dir:
            create_ansible_cfg(temp_dir, distribution.client_url, pulp_admin_user)
            collection_name = "".join([random.choice(string.ascii_lowercase) for i in range(26)])
            cmd = "ansible-galaxy collection init --init-path {} pulp.{}".format(
                temp_dir, collection_name
            )
            subprocess.run(cmd.split())

            collection_meta = os.path.join(temp_dir, f"pulp/{collection_name}/meta")
            os.mkdir(collection_meta)
            with open(os.path.join(collection_meta, "runtime.yml"), "w") as runtime:
                runtime.write('requires_ansible: ">=2.9"')

            cmd = "ansible-galaxy collection build --output-path {} {}{}".format(
                temp_dir, temp_dir, "/pulp/" + collection_name + "/"
            )
            subprocess.run(cmd.split())

            repo_version = ansible_repo_version_api_client.read(repo.latest_version_href)
            print('--------------------')
            print(f'repo: {repo.latest_version_href}')
            assert(repo_version.number == 0)  # We uploaded 1 collection

            cmd = "ansible-galaxy collection publish -c {}{}".format(
                temp_dir, "/pulp-" + collection_name + "-1.0.0.tar.gz"
            )
            subprocess.run(cmd.split(), cwd=temp_dir)
            wait_tasks()

            repo = ansible_repo_api_client.read(repo.pulp_href)
            repo_version = ansible_repo_version_api_client.read(repo.latest_version_href)
            print('bbbbbbbbbbbbbbbbbbbbbbb')
            print(f'repo: {repo.latest_version_href}')
            assert(repo_version.number == 1)  # We uploaded 1 collection


def test_upload_collection_with_requires_ansible(
    ansible_repo_api_client,
    ansible_repo_version_api_client,
    ansible_distribution_factory,
    create_ansible_cfg,
    galaxy_v3_collection_api_client,
    galaxy_v3_collection_versions_api_client,
    gen_object_with_cleanup,
    pulp_admin_user,
):
    """Test whether ansible-galaxy can upload a Collection to Pulp."""
    delete_orphans()
    with pulp_admin_user:
        repo = gen_object_with_cleanup(ansible_repo_api_client, gen_repo())

        # Create a distribution.
        distribution = ansible_distribution_factory(repo)

        collections = galaxy_v3_collection_api_client.list(distribution.base_path)
        assert(collections.meta.count == 0)

        temp_path = f"/tmp/{uuid4()}"
        subprocess.run(f"mkdir -p {temp_path}".split())
        create_ansible_cfg(temp_path, distribution.client_url, pulp_admin_user)

        content = http_get("https://galaxy.ansible.com/download/pulp-squeezer-0.0.9.tar.gz")
        collection_path = f"{temp_path}/pulp-squeezer-0.0.9.tar.gz"
        with open(collection_path, "wb") as f:
            f.write(content)

        cmd = "ansible-galaxy collection publish -c {}".format(collection_path)
        subprocess.run(cmd.split())
        wait_tasks()

        collections = galaxy_v3_collection_api_client.list(distribution.base_path)
        print('000000000000000000')
        print(f'collections: {collections}')
        print('000000000000000000')
        assert(collections.meta.count == 1)

        repo = ansible_repo_api_client.read(repo.pulp_href)
        repo_version = ansible_repo_version_api_client.read(repo.latest_version_href)
        assert(repo_version.number == 1)  # We uploaded 1 collection

        version = galaxy_v3_collection_versions_api_client.read(
            "squeezer", "pulp", distribution.base_path, "0.0.9"
        )

        assert(version.requires_ansible == ">=2.8")
