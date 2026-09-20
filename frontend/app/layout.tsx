import type { Metadata, Viewport } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'ARISTEA-PROCURE | Indian Standards Intelligence & Tender Engine',
  description:
    'AI-powered procurement intelligence platform for Indian Standards (BIS), featuring semantic recommendation, tender document auditing, version supersession tracking, and speech-enabled query workflows.',
  keywords: [
    'Indian Standards',
    'BIS',
    'Procurement Intelligence',
    'Tender Document Audit',
    'IS Standards',
    'QCO Compliance',
    'Framer Motion',
    'GSAP',
  ],
  authors: [{ name: 'ARISTEA-PROCURE Team' }],
};

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
