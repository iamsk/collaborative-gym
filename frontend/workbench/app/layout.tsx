import '@/app/globals.css';
import { Toaster } from 'react-hot-toast';
import { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Trip Planning',
  description: 'Trip Planning for human-AI collaboration',
};



export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>{children}</body>
      <Toaster />
    </html>
  );
}
