from subprocess import CalledProcessError

from test_base import TestBase
from tests.st.utils.docker_host import DockerHost


class TestContainerToHost(TestBase):
    def test_container_to_host(self):
        """
        Test that a container can ping the host.

        This function is important for Mesos, since the containerized executor
        needs to exchange messages with the Mesos Slave process on the host.

        Note also that we do not use the Docker Network driver for this test.
        The Docker Container Network Model defines a "network" as a group of
        endpoints that can communicate with each other, but are isolated from
        everything else.  Thus, an endpoint of a Docker network should not be
        able to ping the host.
        """
        with DockerHost('host', dind=False) as host:
            host.calicoctl("profile add TEST")

            # Use standard docker bridge networking.
            node1 = host.create_workload("node1")

            # Add the nodes to Calico networking.
            host.calicoctl("container add %s 192.168.100.1" % node1)

            # Get the endpoint IDs for the containers
            ep1 = host.calicoctl("container %s endpoint-id show" % node1)

            # Now add the profiles.
            host.calicoctl("endpoint %s profile set TEST" % ep1)

            # Check it works.  Note that the profile allows all outgoing
            # traffic by default, and conntrack should allow the reply.
            node1.assert_can_ping(host.ip, retries=10)
