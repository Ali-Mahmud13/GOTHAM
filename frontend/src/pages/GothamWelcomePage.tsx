import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

export const GothamWelcomePage = () => {
  const navigate = useNavigate();
  const [visible, setVisible] = useState(false);
  const [fadeOut, setFadeOut] = useState(false);

  useEffect(() => {
    // fade in on mount
    const enterTimer = setTimeout(() => setVisible(true), 50);

    // start fade out before navigate
    const exitTimer = setTimeout(() => setFadeOut(true), 1500);

    // navigate after fade out finishes
    const navTimer = setTimeout(() => {
      navigate("/dashboard", { replace: true });
    }, 2050);

    return () => {
      clearTimeout(enterTimer);
      clearTimeout(exitTimer);
      clearTimeout(navTimer);
    };
  }, [navigate]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-blue-50/30 to-pink-50/30 relative overflow-hidden flex items-center justify-center p-4">
      {/* Background Pattern (same aesthetic) */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-gradient-to-br from-medical-pink/20 to-medical-blue/20 rounded-full blur-3xl" />
        <div className="absolute -bottom-40 -left-40 w-96 h-96 bg-gradient-to-tr from-medical-blue/20 to-medical-pink/20 rounded-full blur-3xl" />
      </div>

      {/* Full-page centered branding */}
      <div
        className={[
          "relative z-10 text-center transform transition-all duration-700 ease-out",
          visible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-2",
          fadeOut ? "opacity-0 scale-[0.98]" : "",
        ].join(" ")}
      >
        <div className="inline-flex items-center justify-center mb-5">
          <div className="relative">
            <div className="absolute inset-0 bg-gradient-to-br from-medical-pink to-medical-blue rounded-2xl blur-xl opacity-50 animate-glow-pulse" />
            <div className="relative bg-white p-4 rounded-2xl shadow-lg">
              <img src="/logo.png" alt="GOTHAM Logo" className="h-16 w-16 object-contain" />
            </div>
          </div>
        </div>

        <h1 className="text-4xl sm:text-5xl font-bold bg-gradient-to-r from-medical-pink to-medical-blue bg-clip-text text-transparent">
          Gotham Needs You
        </h1>
        <p className="mt-3 text-gray-600 text-sm sm:text-base">
          Preparing your medical dashboard...
        </p>
      </div>
    </div>
  );
};