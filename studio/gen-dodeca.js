// Genera mark.svg (UI) e icon.svg (app) del dodecaedro con sole facce in vista.
const fs = require("fs");
const phi = (1 + Math.sqrt(5)) / 2, inv = 1 / phi, signs = [-1, 1];
const vertices = [];
for (const x of signs) for (const y of signs) for (const z of signs) vertices.push([x, y, z]);
for (const y of signs) for (const z of signs) vertices.push([0, y * inv, z * phi]);
for (const x of signs) for (const y of signs) vertices.push([x * inv, y * phi, 0]);
for (const x of signs) for (const z of signs) vertices.push([x * phi, 0, z * inv]);
const dist = (a, b) => Math.hypot(a[0]-b[0], a[1]-b[1], a[2]-b[2]);
const edgeLen = Math.min(...vertices.flatMap((a,i) => vertices.slice(i+1).map(b => dist(a,b))));
const adj = vertices.map(() => new Set());
vertices.forEach((a,i) => vertices.forEach((b,j) => {
  if (j > i && Math.abs(dist(a,b) - edgeLen) < 1e-6) { adj[i].add(j); adj[j].add(i); }
}));
const coplanar = ids => {
  const [a,b,c] = ids.map(i => vertices[i]);
  const u = [b[0]-a[0],b[1]-a[1],b[2]-a[2]], v = [c[0]-a[0],c[1]-a[1],c[2]-a[2]];
  const n = [u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0]];
  return Math.hypot(...n) > 1e-6 && ids.every(i =>
    Math.abs((vertices[i][0]-a[0])*n[0]+(vertices[i][1]-a[1])*n[1]+(vertices[i][2]-a[2])*n[2]) < 1e-6);
};
const combos = (start, picked, out) => {
  if (picked.length === 5) { out.push([...picked]); return; }
  for (let i = start; i <= vertices.length - (5 - picked.length); i++) combos(i+1, [...picked, i], out);
};
const all = []; combos(0, [], all);
const faces = all.filter(ids => coplanar(ids) && ids.every(i => ids.filter(j => adj[i].has(j)).length === 2));

const rotate = ([x,y,z]) => {
  const ay = -0.45, ax = 0.62;
  const x1 = x*Math.cos(ay) + z*Math.sin(ay), z1 = -x*Math.sin(ay) + z*Math.cos(ay);
  const y2 = y*Math.cos(ax) - z1*Math.sin(ax), z2 = y*Math.sin(ax) + z1*Math.cos(ax);
  return [x1, y2, z2];
};
const rv = vertices.map(rotate);

// visibilita': camera a +y (la proiezione usa x,z e il painter disegna per y crescente)
// per un poliedro regolare centrato nell'origine la normale uscente e' ∝ centro faccia
const isVisible = ids => ids.reduce((s,i) => s + rv[i][1], 0) / 5 > 0;
const visFaces = faces.filter(isVisible);

function svgFor(size, pad) {
  const xs = rv.map(v => v[0]), zs = rv.map(v => v[2]);
  const minX = Math.min(...xs), maxX = Math.max(...xs), minZ = Math.min(...zs), maxZ = Math.max(...zs);
  const scale = (size - 2*pad) / Math.max(maxX - minX, maxZ - minZ);
  const project = i => {
    const [x,,z] = rv[i];
    return [size/2 + (x-(minX+maxX)/2)*scale, size/2 - (z-(minZ+maxZ)/2)*scale];
  };
  const orderFace = ids => {
    const pts = ids.map(i => ({ i, p: project(i) }));
    const cx = pts.reduce((s,p) => s+p.p[0],0)/5, cz = pts.reduce((s,p) => s+p.p[1],0)/5;
    return pts.sort((a,b) => Math.atan2(a.p[1]-cz,a.p[0]-cx) - Math.atan2(b.p[1]-cz,b.p[0]-cx)).map(p => p.i);
  };
  const ordered = visFaces
    .map(ids => ({ ids: orderFace(ids), depth: ids.reduce((s,i) => s+rv[i][1],0)/5 }))
    .sort((a,b) => a.depth - b.depth);
  const polys = ordered.map((f,i) =>
    `<polygon class="face f${i+1}" points="${f.ids.map(project).map(p => p.map(n => n.toFixed(2)).join(",")).join(" ")}"/>`);
  // spigoli: solo quelli delle facce visibili, senza duplicati
  const seen = new Set(); let edgePath = "";
  for (const f of ordered) for (let k = 0; k < 5; k++) {
    const a = f.ids[k], b = f.ids[(k+1)%5], key = a < b ? a+"-"+b : b+"-"+a;
    if (seen.has(key)) continue; seen.add(key);
    const [x1,z1] = project(a), [x2,z2] = project(b);
    edgePath += `M${x1.toFixed(2)} ${z1.toFixed(2)}L${x2.toFixed(2)} ${z2.toFixed(2)}`;
  }
  return { polys, edgePath };
}

// ---- mark.svg (64x64, stile UI: CSS esterno della pagina) ----
const m = svgFor(64, 8);
fs.writeFileSync(process.argv[2] + "/mark.svg",
  `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" role="img" aria-label="ccllrun Studio">` +
  m.polys.join("") + `<path class="edge" d="${m.edgePath}"/></svg>\n`);

// ---- icon.svg (1024, autonomo: stessi colori del tema) ----
const I = svgFor(1024, 200);
const iconPolys = I.polys.map(p => p
  .replace(/class="face f\d+"/, 'fill="url(#face)" fill-opacity=".30" stroke="#e08b6e" stroke-width="30" stroke-linejoin="round"'));
fs.writeFileSync(process.argv[2] + "/icon.svg",
`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1024 1024">
  <defs>
    <linearGradient id="bg" x1="120" y1="96" x2="904" y2="928" gradientUnits="userSpaceOnUse">
      <stop offset="0" stop-color="#353533"/><stop offset="1" stop-color="#1d1d1b"/>
    </linearGradient>
    <linearGradient id="face" x1="206" y1="132" x2="790" y2="874" gradientUnits="userSpaceOnUse">
      <stop offset="0" stop-color="#e08b6e"/><stop offset="1" stop-color="#c96442"/>
    </linearGradient>
  </defs>
  <rect x="64" y="64" width="896" height="896" rx="224" fill="url(#bg)"/>
  ${iconPolys.join("\n  ")}
  <path d="${I.edgePath}" fill="none" stroke="#f7d8cc" stroke-width="26" stroke-linecap="round" stroke-linejoin="round" opacity=".95"/>
</svg>\n`);
console.log("facce visibili:", visFaces.length);
