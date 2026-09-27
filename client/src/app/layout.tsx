import type { Metadata } from "next";
import type { ReactNode } from "react";
import "./globals.css";

export const metadata: Metadata = {
  title: "Who's That Pokémon?",
  description: "Find the Pokémon that matches your working style.",
  icons: {
    icon: "/pokeMatcherIcon.png",
    shortcut: "/pokeMatcherIcon.png",
    apple: "/pokeMatcherIcon.png",
  },
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html
      lang="en"
      className="h-full antialiased font-sans"
    >
      <body suppressHydrationWarning className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
