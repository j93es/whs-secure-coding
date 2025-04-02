from flask import current_app as app

def register_headers(app):
    @app.after_request
    def set_headers(response):
        if app.config["ENV"] == "production":
            pass
        else:
            return response
            
        # 👉 캐시 관련
        response.headers["Cache-Control"] = "public, max-age=86400"

        # 👉 Content Security Policy
        csp = [
            "default-src 'none'",
            "base-uri 'self'",
            "connect-src 'self'",
            "font-src 'self'",
            "form-action 'self'",
            "frame-ancestors 'none'",
            "img-src 'self'",
            "script-src 'self' cdnjs.cloudflare.com",
            "style-src 'self'",
            "manifest-src 'self'",
            "object-src 'self'",
            "upgrade-insecure-requests"
        ]
        response.headers["Content-Security-Policy"] = "; ".join(csp)

        # 👉 보안 관련 헤더들
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "accelerometer=(),autoplay=(),camera=(),fullscreen=(self),"
            "geolocation=(),gyroscope=(),midi=(),microphone=(),magnetometer=(),"
            "payment=(),xr-spatial-tracking=()"
        )
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        response.headers["Cross-Origin-Embedder-Policy"] = "require-corp"
        response.headers["X-Permitted-Cross-Domain-Policies"] = "none"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        return response

