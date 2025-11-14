import "./globals.css";
import Link from "next/link";
import { NavLink } from "../components/NavLink";

export const metadata = { title: "Allergy Menu Finder" };

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        {/* Skip to main for keyboard/screen readers */}
        <a className="skip-link" href="#main">Skip to main content</a>

        <div className="container">
          <header className="header" role="banner">
            <h1 className="brand">Allergy Menu Finder</h1>

            {/* Accessible nav with aria-current */}
            <nav className="nav" aria-label="Primary">
              <NavLink href="/">Home</NavLink>
              <NavLink href="/login">Login</NavLink>
              <NavLink href="/register">Register</NavLink>
              <NavLink href="/menu">Menu</NavLink>
              <NavLink href="/profile">Profile</NavLink>
              <NavLink href="/upload">Upload</NavLink>
              <NavLink href="/manage">Manage</NavLink>
            </nav>
          </header>

          <main id="main" role="main" className="content">
            {children}
          </main>

          <footer className="small" role="contentinfo" style={{marginTop: 24}}>
            © {new Date().getFullYear()} Allergy Menu Finder • Built for accessibility (WCAG 2.1 AA)
          </footer>
        </div>
      </body>
    </html>
  );
}
