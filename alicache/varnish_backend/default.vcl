#
# This is an example VCL file for Varnish.
#
# It does not do anything by default, delegating control to the
# builtin VCL. The builtin VCL is called when there is no explicit
# return statement.
#
# See the VCL chapters in the Users Guide at https://www.varnish-cache.org/docs/
# and https://www.varnish-cache.org/trac/wiki/VCLExamples for more examples.

# Marker to tell the VCL compiler that this VCL has been adapted to the
# new 4.0 format.
vcl 4.0;

# Default backend definition. Set this to point to your content server.
backend default {
    .host = "ali-ci.cern.ch";
    .port = "80";
}

sub vcl_recv {
    # Happens before we check if we have this in cache already.
    #
    # Typically you clean up the request here, removing cookies you don't need,
    # rewriting the request, etc.
    set req.http.host = "ali-ci.cern.ch";
    unset req.http.cookie;

    # Append trailing slash to every URL except .tar.gz
    #if (! req.url ~ "\.tar\.gz$" && ! req.url ~ "/$") {
    #  set req.url = req.url + "/";
    #}

    # Append trailing slash to every URL whose last component does not look
    # like a filename with extension
    if (! req.url ~ "/[^/]*\.[^/]*$" && ! req.url ~ "/$") {
      set req.url = req.url + "/";
    }
}

sub vcl_backend_response {
    # Happens after we have read the response headers from the backend.
    #
    # Here you clean the response headers, removing silly Set-Cookie headers
    # and other mistakes your backend does.

    # Cache 404 for a short time (one minute)
    # See http://book.varnish-software.com/4.0/chapters/VCL_Basics.html#the-initial-value-of-beresp-ttl
    if (beresp.status == 404) {
        set beresp.ttl = 60s;
    }
}

sub vcl_deliver {
    # Happens when we have all the pieces we need, and are about to send the
    # response to the client.
    #
    # You can do accounting or modifying the final object here.
    if (obj.hits > 0) {
      set resp.http.X-Cache = "HIT";
    } else {
      set resp.http.X-Cache = "MISS";
    }
}
