const lt = require('localtunnel');

(async () => {
  try {
    const tunnel = await lt({ port: 8503 });
    console.log('TUNNEL_URL:' + tunnel.url);
    tunnel.on('close', () => {
      console.log('Tunnel closed');
    });
  } catch (e) {
    console.error('ERROR:', e.message);
  }
})();
