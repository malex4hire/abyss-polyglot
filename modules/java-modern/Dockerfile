# The Maven image is the runtime image on purpose.
#
# There is no host JDK, so `mvn test` runs inside this container against bind-mounted
# source. A slim JRE runtime would make every test run a rebuild, which is slow enough
# that nobody would run the suite.
FROM maven:3.9-eclipse-temurin-25@sha256:1b1fc6d0168ea616afd1c861d6f32ec37c9ec2ffe88a0351b3771dd4ad86b0d8

WORKDIR /app

# Dependencies first, so a source edit does not re-resolve the tree.
COPY pom.xml ./
RUN mvn -B -q dependency:go-offline

# surefire resolves its provider jar at execution time, which needs the network.
# Pulling it explicitly is what lets the suite run in the container with no network.
# The version is read from the pom rather than repeated here. Pinned in two places it
# drifted: the pom moved to a surefire that supports JUnit 6 and this kept fetching the
# old provider, which then could not discover a single test.
RUN SUREFIRE=$(sed -n "s|.*<surefire.version>\(.*\)</surefire.version>.*|\1|p" pom.xml) \
    && mvn -B -q dependency:get -Dartifact=org.apache.maven.surefire:surefire-junit-platform:$SUREFIRE

COPY src ./src
RUN mvn -B -q package -DskipTests

# Run from the exploded classpath rather than a fat jar: the identity endpoint reports
# what actually resolved, and a flattened jar would hide the artifact set that check
# reads. The service compiles the mounted source at start rather than trusting whatever
# is already in target/classes. `mvn test` runs in this container against the bind mount
# and overwrites target/classes with whatever the tree said at that moment, so a later
# restart would otherwise boot code that is in no one's working tree.
# Offline by construction: -o, and every dependency is already in the image.
CMD ["sh", "-lc", "mvn -o -q package -DskipTests && exec java -cp 'target/classes:target/lib/*' com.abyss.polyglot.javamodern.App"]
