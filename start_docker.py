#!/usr/local/bin/python3

import sys
import os
import os.path
import time
import subprocess

kStatusRunning = "running"
kStatusExited = "exited"

# using https://hub.docker.com/_/mysql/
# to use the latest mysql, use mysql:8
imageName = "mysql:5.6"
# name must be unique across containers running on this computer
containerName = "mysql-db-multi"
# this is where mysql database files are stored, so that
# they persist even if container goes away
dbDir = os.path.expanduser("~/data/db-multi")
# 3306 is standard MySQL port, I use a unique port to be able
# to run multiple mysql instances for different projects
dockerDbLocalPort = "7200"


def eprint(*args, **kwargs):
  print(*args, file=sys.stderr, **kwargs)


def print_cmd(cmd):
  eprint("cmd:" + " ".join(cmd))


def run_cmd(cmd):
  print_cmd(cmd)
  res = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  eprint(res.stdout.decode('utf-8'))


def run_cmd_out(cmd):
  print_cmd(cmd)
  s = subprocess.check_output(cmd)
  return s.decode("utf-8")


def run_cmd_show_progress(cmd):
  eprint("Running '%s'" % cmd)
  p = subprocess.Popen(cmd, stdout = subprocess.PIPE,
          stderr = subprocess.STDOUT, shell = True)
  while True:
    line = p.stdout.readline()
    if not line:
      break
    sys.stdout.buffer.write(line)
    sys.stdout.flush()


# print("Finished runnign '%s'" % " ".join(cmd))
def verify_docker_running():
  try:
    run_cmd(["docker", "ps"])
  except:
    eprint("docker is not running! must run docker")
    sys.exit(10)


# not sure if this covers all cases
def decode_status(status_verbose):
  if "Exited" in status_verbose:
    return kStatusExited
  return kStatusRunning


# given:
# 0.0.0.0:7200->3306/tcp
# return (0.0.0.0, 7200) or None if doesn't match
def decode_ip_port(mappings):
  parts = mappings.split("->")
  if len(parts) != 2:
    return None
  parts = parts[0].split(":")
  if len(parts) != 2:
    return None
  return parts


# returns:
#  - container id
#  - status
#  - (ip, port) in the host that maps to exposed port inside the container (or None)
# returns (None, None, None) if no container of that name
def docker_container_info(containerName):
  s = run_cmd_out(["docker", "ps", "-a", "--format", "{{.ID}}|{{.Status}}|{{.Ports}}|{{.Names}}"])
  # this returns a line like:
  # 6c5a934e00fb|Exited (0) 3 months ago|0.0.0.0:7200->3306/tcp|mysql-56-for-quicknotes
  lines = s.split("\n")
  for l in lines:
    if len(l) == 0:
      continue
    parts = l.split("|")
    assert len(parts) == 4, "parts: %s" % parts
    id, status, mappings, names = parts
    if containerName in names:
      status = decode_status(status)
      ip_port = decode_ip_port(mappings)
      return (id, status, ip_port)
  return (None, None, None)


def wait_for_container(containerName):
  # 8 secs is a heuristic
  timeOut = 8
  eprint("waiting %s secs for container to start" % timeOut, end="", flush=True)
  while timeOut > 0:
    (containerId, status, ip_port) = docker_container_info(containerName)
    if status == kStatusRunning:
      return
    eprint(".", end="", flush=True)
    time.sleep(1)
    timeOut -= 1
  eprint("")


def start_container_if_needed(imageName, containerName, portMapping):
  (containerId, status, ip_port) = docker_container_info(containerName)
  if status == kStatusRunning:
    eprint("container %s is already running" % containerName)
    return
  if status == kStatusExited:
    cmd = ["docker", "start", containerId]
  else:
    volumeMapping = "%s:/var/lib/mysql" % dbDir
    cmd = ["docker", "run", "-d", "--name=" + containerName, "-p", portMapping, "-v", volumeMapping, "-e", "MYSQL_ALLOW_EMPTY_PASSWORD=yes", imageName]
  run_cmd(cmd)
  wait_for_container(containerName)


def create_db_dir():
  try:
    os.makedirs(dbDir)
  except:
    # throws if already exists, which is ok
    pass


def main():
  verify_docker_running()
  create_db_dir()
  start_container_if_needed(imageName, containerName, dockerDbLocalPort + ":3306")
  (containerId, status, ip_port) = docker_container_info(containerName)
  assert ip_port is not None
  ip, port = ip_port
  print("%s;%s" % (ip, port))


if __name__ == "__main__":
  main()