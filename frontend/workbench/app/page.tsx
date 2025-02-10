import LandingPage from "@/components/landing-page";
import { server } from "@/mocks/node";


const HomePage = () => {
  if (process.env.NEXT_PUBLIC_USE_MOCK_API === "true") {
    console.log("Using mock API");
    server.listen();
  }
  return (
    <main>
      <LandingPage />
    </main>
  );
};

export default HomePage;
