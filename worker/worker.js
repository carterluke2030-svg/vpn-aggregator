// Cloudflare Worker: serves the right format by client User-Agent.
// Set BASE in Worker settings, e.g. https://raw.githubusercontent.com/USER/REPO/main/out
const SINGBOX_UA = /hiddify|sing-?box|sfa|sfi|karing|nekobox/i;

export default {
  async fetch(request, env) {
    const ua = request.headers.get("user-agent") || "";
    const file = SINGBOX_UA.test(ua) ? "singbox.json" : "sub.txt";
    const upstream = await fetch(`${env.BASE}/${file}`, { cf: { cacheTtl: 120 } });
    return new Response(upstream.body, {
      status: upstream.status,
      headers: {
        "content-type": file.endsWith(".json") ? "application/json" : "text/plain; charset=utf-8",
        "profile-update-interval": "1",
        "profile-title": "my-vpn",
        "cache-control": "no-store",
      },
    });
  },
};
