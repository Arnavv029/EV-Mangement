import { createFileRoute } from "@tanstack/react-router";
import { useEffect } from "react";

export const Route = createFileRoute("/")({
  component: Index,
  head: () => ({
    meta: [
      { title: "HapticEV — Smart EV Charging Made Effortless" },
      {
        name: "description",
        content:
          "Locate nearby EV charging stations, reserve slots instantly, and verify with smart QR — premium EV mobility platform.",
      },
    ],
  }),
});

function Index() {
  useEffect(() => {
    window.location.replace("/pages/landing.html");
  }, []);
  return (
    <div className="flex min-h-screen items-center justify-center bg-background">
      <a
        href="/pages/landing.html"
        className="rounded-full bg-primary px-6 py-3 text-primary-foreground font-semibold shadow-lg"
      >
        Enter HapticEV →
      </a>
    </div>
  );
}
