"use client";

import Link from "next/link";
import { useState } from "react";
import type { Session } from "next-auth";

interface NavBarClientProps {
  session: Session | null;
}

export function NavBarClient({ session }: NavBarClientProps) {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const toggleMobileMenu = () => {
    setIsMobileMenuOpen(!isMobileMenuOpen);
  };

  return (
    <>
      <nav className="bg-slate-900 p-4 text-white shadow-md relative z-50">
        <div className="w-full px-4 md:px-8 flex items-center justify-between">
          <Link href="/" className="text-xl font-bold text-yellow-500">
            ZZZ Drive Discs
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden lg:flex items-center gap-6">
            {session ? (
              <>
                <Link
                  href="/artifacts/recent_list"
                  className="rounded-lg bg-yellow-600 px-4 py-2 font-semibold text-white shadow-md transition-all hover:bg-yellow-500 hover:shadow-yellow-500/20 active:scale-95"
                >
                  My Drive Discs
                </Link>
                <Link
                  href="/artifacts/search"
                  className="rounded-lg bg-yellow-600 px-4 py-2 font-semibold text-white shadow-md transition-all hover:bg-yellow-500 hover:shadow-yellow-500/20 active:scale-95"
                >
                  Search Drive Discs
                </Link>
                <Link
                  href="/artifacts/create"
                  className="rounded-lg bg-yellow-600 px-4 py-2 font-semibold text-white shadow-md transition-all hover:bg-yellow-500 hover:shadow-yellow-500/20 active:scale-95"
                >
                  Add Drive Disc
                </Link>
                <Link
                  href="/artifacts/upload"
                  className="rounded-lg bg-yellow-600 px-4 py-2 font-semibold text-white shadow-md transition-all hover:bg-yellow-500 hover:shadow-yellow-500/20 active:scale-95"
                >
                  Upload JSON
                </Link>
                <Link
                  href="/leveling/search"
                  className="rounded-lg bg-yellow-600 px-4 py-2 font-semibold text-white shadow-md transition-all hover:bg-yellow-500 hover:shadow-yellow-500/20 active:scale-95"
                >
                  Search Leveling
                </Link>
                <Link
                  href="/statistics"
                  className="rounded-lg bg-yellow-600 px-4 py-2 font-semibold text-white shadow-md transition-all hover:bg-yellow-500 hover:shadow-yellow-500/20 active:scale-95"
                >
                  Statistics
                </Link>
                <Link
                  href="/substatistics"
                  className="rounded-lg bg-yellow-600 px-4 py-2 font-semibold text-white shadow-md transition-all hover:bg-yellow-500 hover:shadow-yellow-500/20 active:scale-95"
                >
                  Analytics
                </Link>
                <Link
                  href="/api/auth/signout"
                  className="rounded-lg border border-slate-700 bg-slate-800 px-4 py-2 text-sm font-medium text-slate-300 transition-all hover:border-slate-600 hover:bg-slate-700 hover:text-white active:scale-95"
                >
                  Sign Out
                </Link>
                <span className="text-sm text-gray-400">
                  Welcome, {session.user?.name}
                </span>
              </>
            ) : (
              <Link
                href="/api/auth/signin"
                className="rounded-lg bg-yellow-600 px-4 py-2 font-semibold text-white shadow-md transition-all hover:bg-yellow-500 hover:shadow-yellow-500/20 active:scale-95"
              >
                Sign In
              </Link>
            )}
          </div>

          {/* Mobile Hamburger Button */}
          <button
            onClick={toggleMobileMenu}
            className="lg:hidden flex flex-col gap-1.5 p-2 hover:bg-slate-800 rounded transition-colors"
            aria-label="Toggle menu"
          >
            <span
              className={`block h-0.5 w-6 bg-white transition-all duration-300 ${
                isMobileMenuOpen ? "rotate-45 translate-y-2" : ""
              }`}
            ></span>
            <span
              className={`block h-0.5 w-6 bg-white transition-all duration-300 ${
                isMobileMenuOpen ? "opacity-0" : ""
              }`}
            ></span>
            <span
              className={`block h-0.5 w-6 bg-white transition-all duration-300 ${
                isMobileMenuOpen ? "-rotate-45 -translate-y-2" : ""
              }`}
            ></span>
          </button>
        </div>
      </nav>

      {/* Mobile Sidebar */}
      <div
        className={`fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden transition-opacity duration-300 ${
          isMobileMenuOpen ? "opacity-100" : "opacity-0 pointer-events-none"
        }`}
        onClick={toggleMobileMenu}
      ></div>

      <div
        className={`fixed top-0 right-0 h-full w-80 max-w-[85vw] bg-slate-900 text-white shadow-xl z-50 lg:hidden transition-transform duration-300 ${
          isMobileMenuOpen ? "translate-x-0" : "translate-x-full"
        }`}
      >
        <div className="flex flex-col h-full">
          {/* Mobile Menu Header */}
          <div className="flex items-center justify-between p-4 border-b border-slate-800">
            <span className="text-xl font-bold text-yellow-500">Menu</span>
            <button
              onClick={toggleMobileMenu}
              className="p-2 hover:bg-slate-800 rounded transition-colors"
              aria-label="Close menu"
            >
              <svg
                className="w-6 h-6"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>

          {/* Mobile Menu Content */}
          <div className="flex-1 overflow-y-auto p-4">
            {session ? (
              <div className="flex flex-col gap-3">
                <div className="mb-4 p-3 bg-slate-800 rounded-lg border border-slate-700">
                  <p className="text-sm text-gray-400">Welcome,</p>
                  <p className="font-semibold text-yellow-500">
                    {session.user?.name}
                  </p>
                </div>

                <Link
                  href="/artifacts/recent_list"
                  onClick={toggleMobileMenu}
                  className="w-full rounded-lg bg-yellow-600 px-4 py-3 font-semibold text-white shadow-md transition-all hover:bg-yellow-500 active:scale-95 text-center"
                >
                  My Artifacts
                </Link>
                <Link
                  href="/artifacts/search"
                  onClick={toggleMobileMenu}
                  className="w-full rounded-lg bg-yellow-600 px-4 py-3 font-semibold text-white shadow-md transition-all hover:bg-yellow-500 active:scale-95 text-center"
                >
                  Search Artifacts
                </Link>
                <Link
                  href="/artifacts/create"
                  onClick={toggleMobileMenu}
                  className="w-full rounded-lg bg-yellow-600 px-4 py-3 font-semibold text-white shadow-md transition-all hover:bg-yellow-500 active:scale-95 text-center"
                >
                  Add Artifact
                </Link>
                <Link
                  href="/artifacts/upload"
                  onClick={toggleMobileMenu}
                  className="w-full rounded-lg bg-yellow-600 px-4 py-3 font-semibold text-white shadow-md transition-all hover:bg-yellow-500 active:scale-95 text-center"
                >
                  Upload JSON
                </Link>
                <Link
                  href="/leveling/search"
                  onClick={toggleMobileMenu}
                  className="w-full rounded-lg bg-yellow-600 px-4 py-3 font-semibold text-white shadow-md transition-all hover:bg-yellow-500 active:scale-95 text-center"
                >
                  Search Leveling
                </Link>
                <Link
                  href="/statistics"
                  onClick={toggleMobileMenu}
                  className="w-full rounded-lg bg-yellow-600 px-4 py-3 font-semibold text-white shadow-md transition-all hover:bg-yellow-500 active:scale-95 text-center"
                >
                  Statistics
                </Link>
                <Link
                  href="/substatistics"
                  onClick={toggleMobileMenu}
                  className="w-full rounded-lg bg-yellow-600 px-4 py-3 font-semibold text-white shadow-md transition-all hover:bg-yellow-500 active:scale-95 text-center"
                >
                  Analytics
                </Link>

                <div className="mt-4 pt-4 border-t border-slate-800">
                  <Link
                    href="/api/auth/signout"
                    onClick={toggleMobileMenu}
                    className="w-full rounded-lg border border-slate-700 bg-slate-800 px-4 py-3 text-sm font-medium text-slate-300 transition-all hover:border-slate-600 hover:bg-slate-700 hover:text-white active:scale-95 text-center block"
                  >
                    Sign Out
                  </Link>
                </div>
              </div>
            ) : (
              <Link
                href="/api/auth/signin"
                onClick={toggleMobileMenu}
                className="w-full rounded-lg bg-yellow-600 px-4 py-3 font-semibold text-white shadow-md transition-all hover:bg-yellow-500 active:scale-95 text-center block"
              >
                Sign In
              </Link>
            )}
          </div>
        </div>
      </div>
    </>
  );
}
