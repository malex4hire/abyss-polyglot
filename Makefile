# Entry points. Every target derives its targets from stacks/manifest.yaml.

.PHONY: help demo record-demo render up up-offline down verify verify-host visual delta demo-reset clean

help:               ## this list
	@grep -hE '^[a-z-]+:.*?##' $(MAKEFILE_LIST) \
	  | sed 's/:.*##/\t/' | expand -t22

demo:               ## the walkthrough, on a bare interpreter, with nothing installed
	python3 demo.py

# The README shows demo output above its first heading, and there are two ways to put
# output in a README: type it, or record it. Typing it is a claim about what the program
# prints, and it decays silently. This is the only supported way to produce that artifact.
record-demo:        ## re-record the walkthrough into the README's terminal artifact
	python3 scripts/record_demo.py

render:             ## regenerate everything derived from the manifest and the tokens
	python3 scripts/render-env.py
	python3 scripts/render-app-tokens.py
	python3 scripts/render-side-by-side.py
	python3 scripts/render-readme.py

# Both bring-up targets tear down first, and it is not tidiness.
#
# Postgres holds a pinned address on a declared subnet, because the egress-blocked overlay
# leaves the embedded DNS resolver unable to answer. That pin is applied when a container
# is CREATED and never when an existing one is reconnected to a recreated network, and
# switching between the normal stack and the overlay recreates the network every time.
# Compose then reconnects the running containers, Postgres lands on whatever address is
# free, and the /etc/hosts entry every JVM client was created with still names the old one.
#
# Measured in both directions: overlay-over-normal and normal-over-overlay each left
# spring-boot dead with a Hibernate "unable to determine dialect" error, three layers away
# from the cause, while six other services reported healthy.
#
# `down` without -v, so the Postgres volume survives. Images are cached, so the cost is
# seconds; a demo that comes up wrong in a way this hard to read is not worth them.
up: render          ## bring the whole demo up
	docker compose down --remove-orphans
	# --wait, because `up -d` returns when the containers are created, not when the
	# services answer. A suite started immediately afterwards read connection resets from
	# stacks that were still booting and reported four stacks broken that were merely
	# not up yet.
	docker compose up -d --build --wait

up-offline: render  ## bring the demo up with no route out of the containers
	docker compose -f docker-compose.yml -f docker-compose.offline.yml down --remove-orphans
	docker compose -f docker-compose.yml -f docker-compose.offline.yml up -d --wait

down:               ## stop everything, keep the data
	docker compose down

delta:              ## compute the auto-configuration delta from the two running artifacts
	python3 scripts/compute_delta.py

verify-host:        ## the checks that need nothing running: seconds, no JDK, no Node
	python3 scripts/audit-guards.py
	python3 scripts/audit-names.py
	python3 -m pytest tests -m "not needs_stacks and not needs_docker and not slow"

verify: verify-host ## the whole host suite, against the running demo
	python3 scripts/audit-types.py
	python3 -m pytest tests

visual:             ## browser checks against every frontend the manifest declares
	bash scripts/visual.sh

# Deliberately not invoked by `visual`. demo-reset restarts the in-memory backends, and a
# target you run to confirm the demo works must not be able to take the demo down. The
# checks leave rows behind; that is a dirty list, which is recoverable and visible. A
# backend restarting under a live screen share is neither.
demo-reset:         ## restore the demo to seed state (soft delete only, restarts backends)
	python3 scripts/demo-reset.py

clean:              ## remove generated output; `make render` puts it all back
	rm -rf build side-by-side/dist .env
