import { Link } from "react-router-dom";
import { buttonVariants } from "@/components/ui/button";

export default function NotFoundPage() {
  return (
    <div className="grid min-h-screen place-items-center px-4 text-center">
      <div>
        <h1 className="text-3xl font-bold">This page does not exist</h1>
        <p className="mt-2 text-muted">Check the address, or go back to your dashboard.</p>
        <Link to="/dashboard" className={buttonVariants({ className: "mt-6" })}>Go to dashboard</Link>
      </div>
    </div>
  );
}
