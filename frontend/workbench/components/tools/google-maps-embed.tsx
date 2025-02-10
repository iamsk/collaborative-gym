interface GoogleMapsEmbedProps {
    origin: string;
    destination: string;
    mode: string;
  }
  
  export default function GoogleMapsEmbed({
    origin,
    destination,
    mode,
  }: GoogleMapsEmbedProps): JSX.Element {
    const baseUrl = "https://www.google.com/maps/embed/v1/directions";
    const apiKey = process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY;
    const url = `${baseUrl}?key=${apiKey}&origin=${encodeURIComponent(
      origin
    )}&destination=${encodeURIComponent(destination)}&mode=${mode}`;
  
    return (
      <div className="w-full h-full rounded-2xl overflow-hidden">
        <iframe
          width="100%"
          height="100%"
          loading="lazy"
          allowFullScreen
          referrerPolicy="no-referrer-when-downgrade"
          src={url}
        />
      </div>
    );
  }
  