import { useEffect, useState } from 'react';

interface BatProps {
    id: number;
    delay: number;
}

const Bat = ({ id, delay }: BatProps) => {
    const [position, setPosition] = useState({
        x: Math.random() * 100,
        y: -10,
    });

    useEffect(() => {
        const startDelay = setTimeout(() => {
            const duration = 3000 + Math.random() * 2000;
            const startX = Math.random() * 100;
            const endX = Math.random() * 100;
            const endY = 110;

            setPosition({ x: startX, y: -10 });

            const startTime = Date.now();
            const animate = () => {
                const elapsed = Date.now() - startTime;
                const progress = Math.min(elapsed / duration, 1);

                // Easing function for smooth movement
                const easeProgress = 1 - Math.pow(1 - progress, 3);

                // Add some wave-like horizontal movement
                const waveOffset = Math.sin(progress * Math.PI * 4) * 10;

                setPosition({
                    x: startX + (endX - startX) * easeProgress + waveOffset,
                    y: -10 + endY * easeProgress,
                });

                if (progress < 1) {
                    requestAnimationFrame(animate);
                }
            };

            animate();
        }, delay);

        return () => clearTimeout(startDelay);
    }, [id, delay]);

    return (
        <div
            className="fixed pointer-events-none z-[9999] transition-transform duration-100"
            style={{
                left: `${position.x}%`,
                top: `${position.y}%`,
                transform: 'translate(-50%, -50%)',
            }}
        >
            <svg
                width="40"
                height="40"
                viewBox="0 0 24 24"
                fill="none"
                className="animate-flap drop-shadow-lg"
            >
                <path
                    d="M12 2C10.5 2 9 3 8 4.5C7 3 5.5 2 4 2C2 2 1 3.5 1 5.5C1 7.5 2 9 3 10L8 14L12 17L16 14L21 10C22 9 23 7.5 23 5.5C23 3.5 22 2 20 2C18.5 2 17 3 16 4.5C15 3 13.5 2 12 2Z"
                    fill="currentColor"
                    className="text-gray-900"
                />
                <circle cx="9" cy="7" r="0.8" fill="red" className="animate-pulse" />
                <circle cx="15" cy="7" r="0.8" fill="red" className="animate-pulse" />
            </svg>
        </div>
    );
};

interface BatEasterEggProps {
    onComplete?: () => void;
}

export const BatEasterEgg = ({ onComplete }: BatEasterEggProps) => {
    const [bats, setBats] = useState<number[]>([]);

    useEffect(() => {
        // Create 20-30 bats with staggered delays
        const batCount = 20 + Math.floor(Math.random() * 10);
        const batIds = Array.from({ length: batCount }, (_, i) => i);
        setBats(batIds);

        // Clean up after all animations complete
        const cleanup = setTimeout(() => {
            onComplete?.();
        }, 6000);

        return () => clearTimeout(cleanup);
    }, [onComplete]);

    return (
        <>
            {bats.map((id) => (
                <Bat key={id} id={id} delay={Math.random() * 1000} />
            ))}
            <style>{`
        @keyframes flap {
          0%, 100% {
            transform: scaleX(1) scaleY(1);
          }
          50% {
            transform: scaleX(0.85) scaleY(1.1);
          }
        }
        
        .animate-flap {
          animation: flap 0.3s ease-in-out infinite;
        }
      `}</style>
        </>
    );
};
