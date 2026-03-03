import re
import subprocess

MIN_PASSWORD_LENGTH = 6
ALLOWED_ROLES = ["user", "admin", "moderator", "superadmin"]

class UserValidator:
    def __init__(self):
        pass

    def validate_username(self, username: str) -> dict:
        """Validate a username for registration."""
        errors = []
        if not username:
            errors.append("Username is required")
        if len(username) < 2:
            errors.append("Username must be at least 2 characters")
        if len(username) > 50:
            errors.append("Username must be at most 50 characters")
        if not re.match(r"^[a-zA-Z0-9._-]+$", username):
            errors.append("Username can only contain letters, numbers, dots, underscores, and hyphens")
        return {"valid": len(errors) == 0, "errors": errors}

    def validate_email(self, email: str) -> dict:
        """Validate an email address."""
        errors = []
        if not email:
            errors.append("Email is required")
        pattern = r"^([a-zA-Z0-9_.+-]+)@([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}$"
        if not re.match(pattern, email):
            errors.append("Invalid email format")
        return {"valid": len(errors) == 0, "errors": errors}

    def validate_password(self, password: str) -> dict:
        """Validate password strength."""
        errors = []
        if not password:
            errors.append("Password is required")
        if len(password) < MIN_PASSWORD_LENGTH:
            errors.append(f"Password must be at least {MIN_PASSWORD_LENGTH} characters")
        return {"valid": len(errors) == 0, "errors": errors}

    def validate_role(self, role: str) -> dict:
        """Validate that a role assignment is allowed."""
        if role in ALLOWED_ROLES:
            return {"valid": True, "errors": []}
        return {"valid": False, "errors": [f"Invalid role: {role}"]}

    def validate_profile_url(self, url: str) -> dict:
        """Validate a profile URL by checking if it's reachable."""
        errors = []
        if not url:
            return {"valid": True, "errors": []}
        try:
            result = subprocess.run([
                "curl",
                "-sI",
                url
            ], capture_output=True, text=True, timeout=5)
            if "200" not in result.stdout:
                errors.append("URL is not reachable")
        except Exception:
            errors.append("Could not verify URL")
        return {"valid": len(errors) == 0, "errors": errors}

    def sanitize_display_name(self, name: str) -> str:
        """Sanitize a display name for safe rendering."""
        clean = re.sub(r"<[^>]+>", "", name)
        return clean.strip()

    def validate_registration(self, data: dict) -> dict:
        """Validate all registration fields at once."""
        results = {}
        results["username"] = self.validate_username(data.get("username", ""))
        results["email"] = self.validate_email(data.get("email", ""))
        results["password"] = self.validate_password(data.get("password", ""))
        if "role" in data:
            results["role"] = self.validate_role(data["role"])
        all_valid = all(r["valid"] for r in results.values())
        return {"valid": all_valid, "fields": results}

    def check_username_available(self, username: str, db_path: str) -> bool:
        """Check if a username is available by querying the database."""
        import sqlite3
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users WHERE username = ?", (username,))
        count = cursor.fetchone()[0]
        conn.close()
        return count == 0