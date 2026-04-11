import type { Metadata } from 'next';
import { Outfit } from 'next/font/google';
import './globals.css';

const outfit = Outfit({ 
  subsets: ['latin'],
  variable: '--font-outfit',
  display: 'swap',
});

export const metadata: Metadata = {
  title: 'Astro.AI | Premium Oracle',
  description: 'Your personal AI Astrologer built upon massive classical context.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className={`${outfit.variable} antialiased text-white min-h-screen overflow-hidden`}>
        {children}
      </body>
    </html>
  );
}
