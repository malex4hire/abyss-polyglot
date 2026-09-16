# Entry points. Every target derives its targets from stacks/manifest.yaml.

.PHONY: help demo render up up-offline down verify verify-host visual delta demo-reset clean

help:               ## this list
	@grep -hE '^[a-z-]+:.*?##' $(MAKEFILE_LIST) \
	  | sed 's/:.*##/\t/' | expand -t22

demo:               ## the walkthrough, on a bare interpreter, with nothing installed
	python3 demo.py

render:             ## regenerate everything derived from the manifest and the tokens
	python3 scripts/render-env.py
	python3 scripts/render-app-tokens.py
	python3 scripts/render-side-by-side.py
	python3 scripts/render-readme.py

up: render          ## bring the whole demo up
	# --wait, because `up -d` returns when the containers are created, not when the
	# services answer. A suite started immediately afterwards read connection resets from
	# stacks that were still booting and reported four stacks broken that were merely
	# not up yet.
	docker compose up -d --build --wait

up-offline: render  ## bring the demo up with no route out of the containers
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
