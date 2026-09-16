# The test suite runs vitest inside this container against bind-mounted source, so the
# image carries the toolchain rather than only a built bundle.
FROM node:24-slim@sha256:3638d9a6fe4030bd716be989438248074489337ba3275657f93595428be4fc03
WORKDIR /app
COPY package.json ./
RUN npm install --no-audit --no-fund
COPY tsconfig.json vite.config.ts index.html ./
COPY src ./src

# Build the bundle at image build time, and record what actually resolved so the
# instrumentation endpoint can report it without a toolchain running.
RUN npm run build \
 && node -e "const {readdirSync,readFileSync,writeFileSync}=require('fs');const out=[];const walk=(d,p='')=>{for(const e of readdirSync(d)){const n=p?p+'/'+e:e;if(e.startsWith('@')&&!p){walk(d+'/'+e,e);continue;}try{const m=JSON.parse(readFileSync(d+'/'+e+'/package.json','utf8'));if(m.name&&m.version)out.push(m.name+'@'+m.version);}catch{}}};walk('node_modules');out.sort();writeFileSync('artifacts.json',JSON.stringify(out));"

COPY serve.mjs ./
EXPOSE 8080
# Build the mounted source at start, then serve it. dist is produced at image build,
# and every edit lands in the bind mount — so a container serving the baked dist serves
# whatever the source looked like when the image was made. Recreating the container
# silently reverted the application to an older build twice while this was being written.
CMD ["sh", "-lc", "npm run build && RESOLVED_ARTIFACTS=$(cat artifacts.json) exec node serve.mjs"]
