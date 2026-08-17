import type { Metadata } from 'next';
import { Outfit } from 'next/font/google';
import './globals.css';

const outfit = Outfit({ 
  subsets: ['latin'],
  variable: '--font-outfit',
  display: 'swap',
});

export const metadata: Metadata = {
  title: 'Jyotish Oracle | Astro.AI',
  description: 'Your personal AI Jyotish Astrologer — classical Vedic wisdom powered by precision computation.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="h-full">
      <body className={`${outfit.variable} antialiased h-full overflow-hidden`}>
        {children}
      </body>
    </html>
  );
}
