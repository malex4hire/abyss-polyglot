# Maven is the runtime image on purpose: the test suite runs `mvn test` in this container
# against bind-mounted source, so a slim JRE would make every iteration a rebuild.
FROM maven:3.9-eclipse-temurin-25@sha256:1b1fc6d0168ea616afd1c861d6f32ec37c9ec2ffe88a0351b3771dd4ad86b0d8
WORKDIR /app
# Built from the repo root (see docker-compose.yml's build.context for this service) so
# this can COPY wait-for-postgres.sh, shared with spring-traditional below.
COPY modules/spring-boot/pom.xml ./
RUN mvn -B -q dependency:go-offline
# surefire resolves its provider jar at execution time, which needs the network.
# Pulling it explicitly is what lets the in-container test suite run with no network.
# The version is read from the pom rather than repeated here. Pinned in two places it
# drifted: the pom moved to a surefire that supports JUnit 6 and this kept fetching the
# old provider, which then could not discover a single test.
RUN SUREFIRE=$(sed -n "s|.*<surefire.version>\(.*\)</surefire.version>.*|\1|p" pom.xml) \
    && mvn -B -q dependency:get -Dartifact=org.apache.maven.surefire:surefire-junit-platform:$SUREFIRE

COPY modules/spring-boot/src ./src
COPY scripts/wait-for-postgres.sh /usr/local/bin/wait-for-postgres.sh
RUN chmod +x /usr/local/bin/wait-for-postgres.sh
# Tests are skipped at image build: most need the database, and the suite is run in the
# running container, where Postgres is reachable.
RUN mvn -B -q package -DskipTests
# The service compiles the mounted source at start rather than trusting whatever is
# already in target/classes. Running `mvn test` in this container builds the bind mount
# into target/classes, so those classes reflect whatever the tree held at that moment;
# editing the source back does not rebuild them, and a later restart would otherwise boot
# code that matches no working tree.
# Offline by construction: -o, and every dependency is already in the image.
#
# 2026-08-14: wait-for-postgres.sh bounds the wait for the embedded DNS
# resolver at container start (see the script for why). docker-compose.yml's healthcheck
# retries budget for this service was widened to cover the wait it can add.
CMD ["sh", "-lc", "wait-for-postgres.sh postgres 30 && mvn -o -q package -DskipTests && exec java -cp 'target/classes:target/lib/*' com.abyss.polyglot.springboot.Application"]
