Despite not developing very many "web services" in my career, I have ended up
using HTTP clients and servers, (and even _writing_ HTTP clients and servers),
quite often. In my experience, HTTP (well, specifically versions 1.0 and 1.1)
is nearly ubiquitous, relatively easy to implement, and incredibly useful to
have as a common denominator across many languages and tools you might find
yourself having to put up with.

I wanted to share a motivating example of why HTTP is useful, why you might
want to embed servers in other services, and how you could get started writing
code that accomplishes that. We'll be using [Python
3.10](https://www.python.org/downloads/source/) and only the standard library
on a Linux platform, specifically [`Pop!_OS`](https://pop.system76.com/) 20.04
LTS.

{% danger(title="Production Use") %} If you are writing a production
user-facing application, or anything that listens for connections over the
public internet, you should almost certainly _NOT_ be implementing these
libraries[^diy-servers] based on this article. You should use a
production-tested library and make sure to do due diligence in how to secure
public internet servers, run production services, etc if you have a job or
revenue stream depending on this. {% end %}

Lets start from some this piece of information: HTTP is the language spoken
by clients (usually web browsers) and web servers (the thing listening/waiting
for clients) to exchange or _transfer_hyper text_ (HTTP being _hyper text
transfer protocol_). So this is a language or protocol that both sides will
need to adhere to to be "speaking HTTP". Given that knowledge, when I first
looked at doing this, I started with "what is the simplest conversation over
HTTP that I can replicate at my desktop?".

## Finding a Minimal Example

On most Linux machines, the excellent command-line tool [curl](https://curl.se/)
will be available, which we can combine with Python's built-in HTTP server. In
separate terminals, run:

```sh
$ python -m http.server
```

and

```sh
$ curl -v http://localhost:8000
```

Curl is an HTTP (among other things) client, so its making a real HTTP request
against the Python server. In the terminal running `curl` you'll see something like:

```
* Connected to localhost (127.0.0.1) port 8000 (#0)
> GET / HTTP/1.1
> Host: localhost:8000
> User-Agent: curl/7.74.0
> Accept: */*
>
* Mark bundle as not supporting multiuse
* HTTP 1.0, assume close after body
< HTTP/1.0 200 OK
< Server: SimpleHTTP/0.6 Python/3.10.1
< Date: Sun, 02 Jan 2022 19:38:27 GMT
< Content-type: text/html; charset=utf-8
< Content-Length: 416
<
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">
<html>
...
```

Curl uses `>` on the "verbose" lines to indicate its _sending_ that data to the
server and `<` to indicate data its received from the server. Towards the end,
we can see some stuff that looks like HTML, which is great! That means we're
looking at an exchange of data that our browsers will be doing as well. Feel
free to visit [http://localhost:8000](http://localhost:8000) to double check.

So we've got an example conversion, a way to test our server (that `curl`
command) when we write it, and some small understanding of the data clients and
servers exchange. However, computers are not approximate, we need to understand
_precisely_ what data must be exchanged (what separates those lines of data?
how does the server know when a request is "complete" and ready to be
processed?). For this, the authoritative reference is [the specification
itself](https://datatracker.ietf.org/doc/html/rfc2616#page-35).


[^diy-servers]: Obviously _someone_ has to write these things at some point. If
  you're interested in doing this, please read the above danger callout as my
  advice regarding how careful and thorough you must be to accomplish this. I'd
  very much like to _not_ gatekeep about who can/should write libraries or
  production software - I'm trying to emphasize that since they are often
  facing the public internet, there are real security implications from getting
  things wrong, as well as possibly undertaking unnecessary engineering risk
  from relying on a non-production quality foundational library that your
  business may rely on.
