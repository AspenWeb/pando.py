###############################
 Deploying a Pando application
###############################

Pando applications are standard WSGI applications and should work with any WSGI
server, for example `Gunicorn <https://gunicorn.org/>`_.

*********************
 Client IP addresses
*********************

If your application uses the :attr:`pando.http.request.Request.source` property,
then you need to ensure that the `trusted_proxies` attribute of the `website`
object is correctly set. Here are a few examples:

- If you don't use any reverse proxy, then `trusted_proxies` should be left empty.
- If you use `cloudflared`_, then `trusted_proxies` should also be left empty.
- If you only use local-network load balancers, then you can set `trusted_proxies`
  to :obj:`[['private']]`.
- If you use proxies at specific IP addresses, then `trusted_proxies` should
  contain those addresses, e.g. :obj:`[['x.x.x.x', 'y.y.y.y']]`.
- If you use both of the above, then `trusted_proxies` should contain the two
  lists, i.e. :obj:`[['private'], ['x.x.x.x', 'y.y.y.y']]`.

.. _cloudflared: https://github.com/cloudflare/cloudflared
