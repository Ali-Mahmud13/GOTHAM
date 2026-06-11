import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { motion, useScroll, useTransform, AnimatePresence } from "framer-motion";
import { useRef, useState } from "react";
import {
    Brain,
    Users,
    Activity,
    ArrowRight,
    CheckCircle2,
    Sparkles,
    BrainCircuit,
    Clock
} from "lucide-react";

const features = [
    {
        icon: Brain,
        title: "Five-Model Risk Suite",
        description: "Assesses Gestational Diabetes, Preeclampsia, Anemia, Fetal CTG health, and Fetal Ultrasound anomalies — each with a confidence score and AI-generated clinical report.",
        gradient: "from-medical-pink to-medical-pink-light",
    },
    {
        icon: Activity,
        title: "Multi-Agent AI Pipeline",
        description: "An 11-node LangGraph graph routes queries, runs maternal and fetal models in parallel, retrieves evidence from a Pinecone medical knowledge base, and generates structured clinical responses.",
        gradient: "from-medical-blue to-medical-blue-light",
    },
    {
        icon: Users,
        title: "Patient Portal",
        description: "Patients find and register with a doctor, book or reschedule appointments, view clinical notes, and track their risk history — all from a dedicated self-service portal.",
        gradient: "from-medical-pink to-medical-blue",
    },
    {
        icon: Sparkles,
        title: "Voice-Enabled Data Entry",
        description: "Clinical dictation via Groq Whisper (English + Urdu/Minglish) lets clinicians capture vitals and notes hands-free, with an automatic local fallback.",
        gradient: "from-medical-blue to-medical-pink",
    },
];

const stats = [
    { value: "5", label: "ML Models" },
    { value: "98%", label: "Model Accuracy" },
    { value: "11", label: "Agent Nodes" },
    { value: "2", label: "Languages" },
];

const steps = [
    {
        number: "01",
        title: "Doctor Onboarding",
        description: "Create a verified account, configure your weekly availability, and start accepting patient registration requests.",
    },
    {
        number: "02",
        title: "Patient Registration",
        description: "Patients find a doctor, request registration, and book appointments directly through the patient portal.",
    },
    {
        number: "03",
        title: "AI-Driven Assessment",
        description: "Enter or dictate clinical data. The AI pipeline automatically selects and runs the relevant models in parallel.",
    },
    {
        number: "04",
        title: "Insights & Action",
        description: "Receive risk classifications, confidence scores, evidence-backed recommendations, and a full risk-trend dashboard.",
    },
];

export const LandingPage = () => {
    const navigate = useNavigate();
    const heroRef = useRef(null);
    const [showPrivacy, setShowPrivacy] = useState(false);
    const [showTerms, setShowTerms] = useState(false);
    const [showContact, setShowContact] = useState(false);
    const { scrollYProgress } = useScroll({
        target: heroRef,
        offset: ["start start", "end start"]
    });

    const heroY = useTransform(scrollYProgress, [0, 1], [0, 150]);
    const heroOpacity = useTransform(scrollYProgress, [0, 0.5], [1, 0]);

    return (
        <div className="min-h-screen bg-background overflow-hidden">
            {/* Navigation */}
            <motion.nav
                initial={{ y: -100 }}
                animate={{ y: 0 }}
                transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
                className="fixed top-0 left-0 right-0 z-50 bg-background/80 backdrop-blur-xl border-b border-border/50"
            >
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex items-center justify-between h-16">
                        <motion.div
                            className="flex items-center gap-3"
                            whileHover={{ scale: 1.02 }}
                            transition={{ type: "spring", stiffness: 400, damping: 10 }}
                        >
                            <div className="relative">
                                <div className="absolute inset-0 bg-gradient-to-br from-medical-pink to-medical-blue rounded-lg blur-md opacity-20 animate-glow-pulse" />
                                <div className="relative p-1 rounded-lg">
                                    <img src="/logo.png" alt="GOTHAM Logo" className="h-8 w-8 object-contain" />
                                </div>
                            </div>
                            <div>
                                <h1 className="text-xl font-bold bg-gradient-to-r from-medical-pink to-medical-blue bg-clip-text text-transparent">
                                    GOTHAM
                                </h1>
                                <p className="text-[10px] text-muted-foreground -mt-1">Antenatal Risk Platform</p>
                            </div>
                        </motion.div>
                        <div className="hidden md:flex items-center gap-8">
                            {[
                                { label: "Features", href: "#features" },
                                { label: "How It Works", href: "#how-it-works" },
                                { label: "About", href: "#about" }
                            ].map((item, i) => (
                                <motion.a
                                    key={item.label}
                                    href={item.href}
                                    className="text-sm text-muted-foreground hover:text-foreground transition-colors relative group"
                                    whileHover={{ y: -2 }}
                                    initial={{ opacity: 0, y: -10 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    transition={{ delay: 0.1 * i }}
                                >
                                    {item.label}
                                    <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-gradient-to-r from-medical-pink to-medical-blue group-hover:w-full transition-all duration-300" />
                                </motion.a>
                            ))}
                        </div>
                        <div className="flex items-center gap-3">
                            <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
                                <Button
                                    onClick={() => navigate("/patient/login")}
                                    variant="outline"
                                    className="border-medical-blue/50 text-medical-blue hover:bg-medical-blue/10"
                                >
                                    Patient Portal
                                </Button>
                            </motion.div>
                            <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
                                <Button
                                    onClick={() => navigate("/doctor/login")}
                                    variant="outline"
                                    className="border-border/50 hover:bg-card/50"
                                >
                                    Doctor Login
                                </Button>
                            </motion.div>
                            <motion.div
                                whileHover={{ scale: 1.05 }}
                                whileTap={{ scale: 0.95 }}
                            >
                                <Button
                                    onClick={() => navigate("/doctor/signup")}
                                    className="relative overflow-hidden bg-gradient-to-r from-medical-pink to-medical-blue hover:opacity-90 text-white shadow-lg shadow-medical-pink/25 group"
                                >
                                    <span className="relative z-10">Get Started</span>
                                    <motion.div
                                        className="absolute inset-0 bg-gradient-to-r from-medical-blue to-medical-pink"
                                        initial={{ x: "100%" }}
                                        whileHover={{ x: 0 }}
                                        transition={{ duration: 0.3 }}
                                    />
                                </Button>
                            </motion.div>
                        </div>
                    </div>
                </div>
            </motion.nav>

            {/* Hero Section */}
            <section ref={heroRef} className="relative pt-32 pb-20 px-4 sm:px-6 lg:px-8">
                {/* Background Effects */}
                <div className="absolute inset-0 overflow-hidden">
                    <div className="absolute top-20 left-1/4 w-96 h-96 bg-medical-pink/20 rounded-full blur-3xl animate-pulse" />
                    <div className="absolute bottom-20 right-1/4 w-96 h-96 bg-medical-blue/20 rounded-full blur-3xl animate-pulse" style={{ animationDelay: "1s" }} />
                    <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-gradient-to-r from-medical-pink/10 to-medical-blue/10 rounded-full blur-3xl" />
                </div>

                <motion.div
                    className="relative max-w-7xl mx-auto"
                    style={{ y: heroY, opacity: heroOpacity }}
                >
                    <div className="text-center max-w-4xl mx-auto">
                        <motion.div
                            className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-card border border-border/50 shadow-soft mb-8"
                            initial={{ opacity: 0, y: 20, scale: 0.9 }}
                            animate={{ opacity: 1, y: 0, scale: 1 }}
                            transition={{ duration: 0.6 }}
                            whileHover={{ scale: 1.05 }}
                        >
                            <Sparkles className="h-4 w-4 text-medical-pink" />
                            <span className="text-sm text-muted-foreground">AI-Powered Antenatal Care</span>
                        </motion.div>

                        <motion.h1
                            className="text-4xl sm:text-5xl lg:text-7xl font-bold text-foreground mb-6"
                            initial={{ opacity: 0, y: 30 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ duration: 0.8, delay: 0.1 }}
                        >
                            AI-Powered{" "}
                            <motion.span
                                className="bg-gradient-to-r from-medical-pink via-medical-pink-light to-medical-blue bg-clip-text text-transparent"
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                transition={{ delay: 0.3 }}
                            >
                                Antenatal Risk Assessment
                            </motion.span>
                        </motion.h1>

                        <motion.p
                            className="text-lg sm:text-xl text-muted-foreground mb-10 max-w-2xl mx-auto"
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ duration: 0.6, delay: 0.3 }}
                        >
                            A research prototype combining multi-agent systems, RAG, and machine learning to predict                                                  
                              maternal health risks with explainable AI insights
                        </motion.p>

                        <motion.div
                            className="flex flex-col sm:flex-row items-center justify-center gap-4"
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ duration: 0.6, delay: 0.5 }}
                        >
                            <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.98 }}>
                                <Button
                                    size="lg"
                                    onClick={() => navigate("/doctor/signup")}
                                    className="group bg-gradient-to-r from-medical-pink to-medical-blue hover:opacity-90 text-white shadow-xl shadow-medical-pink/30 px-8"
                                >
                                    <span className="flex items-center">
                                        Get Started
                                        <motion.span
                                            className="ml-2"
                                            animate={{ x: [0, 4, 0] }}
                                            transition={{ duration: 1.5, repeat: Infinity }}
                                        >
                                            <ArrowRight className="h-4 w-4" />
                                        </motion.span>
                                    </span>
                                </Button>
                            </motion.div>
                            <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.98 }}>
                                <Button
                                    size="lg"
                                    variant="outline"
                                    onClick={() => document.getElementById('features')?.scrollIntoView({ behavior: 'smooth' })}
                                    className="border-border/50 hover:bg-card/50"
                                >
                                    Learn More
                                </Button>
                            </motion.div>
                        </motion.div>

                        {/* Tech Stack Badge - Option 2 */}
                        <motion.div
                            className="mt-16 relative"
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ duration: 0.6, delay: 0.7 }}
                        >
                            <div className="flex flex-wrap items-center justify-center gap-3">
                                <span className="text-sm text-muted-foreground">Built with</span>
                                {[
                                    { name: "React", color: "from-medical-blue to-medical-blue-light" },
                                    { name: "FastAPI", color: "from-medical-pink to-medical-pink-light" },
                                    { name: "LangGraph", color: "from-medical-pink to-medical-blue" },
                                    { name: "PostgreSQL", color: "from-medical-blue to-medical-pink" },
                                ].map((tech, i) => (
                                    <motion.div
                                        key={tech.name}
                                        initial={{ opacity: 0, scale: 0.8 }}
                                        animate={{ opacity: 1, scale: 1 }}
                                        transition={{ delay: 0.8 + i * 0.1 }}
                                        whileHover={{ scale: 1.05, y: -2 }}
                                        className="group relative"
                                    >
                                        <div className={`absolute inset-0 bg-gradient-to-r ${tech.color} rounded-full blur opacity-0 group-hover:opacity-20 transition duration-300`} />
                                        <div className="relative px-4 py-1.5 rounded-full bg-card/60 backdrop-blur-sm border border-border/30 hover:border-border/50 transition-colors">
                                            <span className={`text-sm font-medium bg-gradient-to-r ${tech.color} bg-clip-text text-transparent`}>
                                                {tech.name}
                                            </span>
                                        </div>
                                    </motion.div>
                                ))}
                            </div>
                        </motion.div>
                    </div>
                </motion.div>
            </section>

            {/* Stats Section */}
            <section className="py-16 px-4 sm:px-6 lg:px-8 border-y border-border/50 bg-card/30 relative overflow-hidden">
                <motion.div
                    className="absolute inset-0 bg-gradient-to-r from-medical-pink/5 via-transparent to-medical-blue/5"
                    animate={{ x: ["-100%", "100%"] }}
                    transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
                />
                <div className="max-w-7xl mx-auto relative">
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
                        {stats.map((stat, index) => (
                            <motion.div
                                key={index}
                                initial={{ opacity: 0, y: 20 }}
                                whileInView={{ opacity: 1, y: 0 }}
                                transition={{ delay: index * 0.1 }}
                                viewport={{ once: true }}
                                whileHover={{ scale: 1.05 }}
                                className="text-center"
                            >
                                <p className="text-3xl sm:text-4xl font-bold bg-gradient-to-r from-medical-pink to-medical-blue bg-clip-text text-transparent">
                                    {stat.value}
                                </p>
                                <p className="text-sm text-muted-foreground mt-1">{stat.label}</p>
                            </motion.div>
                        ))}
                    </div>
                </div>
            </section>

            {/* Features Section */}
            <section id="features" className="py-24 px-4 sm:px-6 lg:px-8">
                <div className="max-w-7xl mx-auto">
                    <motion.div
                        className="text-center mb-16"
                        initial={{ opacity: 0, y: 20 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: true }}
                    >
                        <motion.span
                            className="inline-block px-4 py-1.5 rounded-full bg-medical-pink/10 text-medical-pink text-sm font-medium mb-4"
                            whileHover={{ scale: 1.05 }}
                        >
                            Features
                        </motion.span>
                        <h2 className="text-3xl sm:text-4xl font-bold text-foreground mb-4">
                            Key Technical{" "}
                            <span className="bg-gradient-to-r from-medical-pink to-medical-blue bg-clip-text text-transparent">
                                Features
                            </span>
                        </h2>
                        <p className="text-muted-foreground max-w-2xl mx-auto">
                            This research prototype demonstrates advanced AI techniques for maternal health risk assessment.
                        </p>
                    </motion.div>

                    <div className="grid md:grid-cols-2 gap-6">
                        {features.map((feature, index) => (
                            <motion.div
                                key={index}
                                initial={{ opacity: 0, y: 40 }}
                                whileInView={{ opacity: 1, y: 0 }}
                                transition={{ delay: index * 0.1 }}
                                viewport={{ once: true }}
                                whileHover={{ y: -8, scale: 1.02 }}
                                className="group relative bg-card/60 backdrop-blur-xl rounded-2xl p-8 border border-border/30 hover:border-medical-pink/30 transition-all duration-500 h-full overflow-hidden"
                            >
                                <motion.div
                                    className={`absolute inset-0 bg-gradient-to-br ${feature.gradient} opacity-0 group-hover:opacity-5 transition-opacity duration-500`}
                                />
                                <div className="relative z-10">
                                    <motion.div
                                        className={`inline-flex p-3 rounded-xl bg-gradient-to-r ${feature.gradient} mb-4`}
                                        whileHover={{ scale: 1.1, rotate: 5 }}
                                        transition={{ type: "spring", stiffness: 400 }}
                                    >
                                        <feature.icon className="h-6 w-6 text-white" />
                                    </motion.div>
                                    <h3 className="text-xl font-semibold text-foreground mb-2">{feature.title}</h3>
                                    <p className="text-muted-foreground">{feature.description}</p>
                                </div>
                            </motion.div>
                        ))}
                    </div>
                </div>
            </section>

            {/* How It Works Section */}
            <section id="how-it-works" className="py-24 px-4 sm:px-6 lg:px-8 bg-card/30">
                <div className="max-w-7xl mx-auto">
                    <motion.div
                        className="text-center mb-16"
                        initial={{ opacity: 0, y: 20 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: true }}
                    >
                        <motion.span
                            className="inline-block px-4 py-1.5 rounded-full bg-medical-blue/10 text-medical-blue text-sm font-medium mb-4"
                            whileHover={{ scale: 1.05 }}
                        >
                            Process
                        </motion.span>
                        <h2 className="text-3xl sm:text-4xl font-bold text-foreground mb-4">
                            System{" "}
                            <span className="bg-gradient-to-r from-medical-pink to-medical-blue bg-clip-text text-transparent">
                                Architecture
                            </span>
                        </h2>
                        <p className="text-muted-foreground max-w-2xl mx-auto">
                            A streamlined workflow from data entry to risk assessment with AI-powered insights.
                        </p>
                    </motion.div>

                    <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
                        {steps.map((step, index) => (
                            <motion.div
                                key={index}
                                className="relative h-full"
                                initial={{ opacity: 0, y: 20 }}
                                whileInView={{ opacity: 1, y: 0 }}
                                transition={{ delay: index * 0.1 }}
                                viewport={{ once: true }}
                                whileHover={{ y: -8 }}
                            >
                                {index < steps.length - 1 && (
                                    <div className="hidden lg:block absolute top-8 left-full w-full h-px bg-gradient-to-r from-border to-transparent z-0" />
                                )}
                                <div className="relative bg-card rounded-2xl p-6 border border-border/50 hover:border-medical-pink/30 transition-all duration-300 h-full">
                                    <span className="text-5xl font-bold bg-gradient-to-r from-medical-pink/20 to-medical-blue/20 bg-clip-text text-transparent">
                                        {step.number}
                                    </span>
                                    <h3 className="text-lg font-semibold text-foreground mt-4 mb-2">{step.title}</h3>
                                    <p className="text-sm text-muted-foreground">{step.description}</p>
                                </div>
                            </motion.div>
                        ))}
                    </div>
                </div>
            </section>

            {/* Benefits Section */}
            <section id="about" className="py-24 px-4 sm:px-6 lg:px-8">
                <div className=" max-w-7xl mx-auto">
                    <div className="grid lg:grid-cols-2 gap-16 items-center">
                        <motion.div
                            initial={{ opacity: 0, x: -20 }}
                            whileInView={{ opacity: 1, x: 0 }}
                            viewport={{ once: true }}
                        >
                            <motion.span
                                className="inline-block px-4 py-1.5 rounded-full bg-medical-pink/10 text-medical-pink text-sm font-medium mb-4"
                                whileHover={{ scale: 1.05 }}
                            >
                                Platform
                            </motion.span>
                            <h2 className="text-3xl sm:text-4xl font-bold text-foreground mb-6">
                                Platform{" "}
                                <span className="bg-gradient-to-r from-medical-pink to-medical-blue bg-clip-text text-transparent">
                                    at a Glance
                                </span>
                            </h2>
                            <p className="text-muted-foreground mb-8">
                                GOTHAM integrates clinical decision support, intelligent scheduling, and a patient-facing
                                portal into a single coherent system — built for OB/GYN clinics managing high-risk antenatal cases.
                            </p>
                            <ul className="space-y-4">
                                {[
                                    "Parallel model execution for faster clinical turnaround",
                                    "RAG over curated medical literature (Pinecone, 768-dim)",
                                    "Doctor verification and admin approval workflow",
                                    "Risk trend charts and weekly assessment history",
                                    "Patient risk stratification: Low / Medium / High",
                                    "Structured result persistence with per-visit ML snapshots",
                                ].map((item, index) => (
                                    <motion.li
                                        key={index}
                                        className="flex items-center gap-3"
                                        initial={{ opacity: 0, x: -20 }}
                                        whileInView={{ opacity: 1, x: 0 }}
                                        transition={{ delay: index * 0.1 }}
                                        viewport={{ once: true }}
                                    >
                                        <motion.div
                                            className="flex-shrink-0 w-6 h-6 rounded-full bg-gradient-to-r from-medical-pink to-medical-blue flex items-center justify-center"
                                            whileHover={{ scale: 1.2 }}
                                        >
                                            <CheckCircle2 className="h-4 w-4 text-white" />
                                        </motion.div>
                                        <span className="text-foreground">{item}</span>
                                    </motion.li>
                                ))}
                            </ul>
                        </motion.div>

                        <motion.div
                            initial={{ opacity: 0, x: 20 }}
                            whileInView={{ opacity: 1, x: 0 }}
                            viewport={{ once: true }}
                        >
                            <div className="relative">
                                <div className="absolute inset-0 bg-gradient-to-r from-medical-pink/30 to-medical-blue/30 rounded-3xl blur-3xl" />
                                <motion.div
                                    className="relative bg-card rounded-3xl border border-border/50 p-8 shadow-2xl"
                                    whileHover={{ y: -8 }}
                                    transition={{ type: "spring", stiffness: 200 }}
                                >
                                    <div className="flex items-center gap-4 mb-6">
                                        <motion.div
                                            className="p-3 rounded-xl bg-gradient-to-r from-medical-pink to-medical-blue"
                                            whileHover={{ rotate: 10, scale: 1.1 }}
                                        >
                                            <BrainCircuit className="h-6 w-6 text-white" />
                                        </motion.div>
                                        <div>
                                            <h3 className="font-semibold text-foreground">Clinical Intelligence</h3>
                                            <p className="text-sm text-muted-foreground">Built for OB/GYN clinics</p>
                                        </div>
                                    </div>
                                    <div className="space-y-4">
                                        {[
                                            { label: "ML Models", value: "5" },
                                            { label: "Model Accuracy", value: "98%" },
                                            { label: "Agent Nodes", value: "11" },
                                        ].map((item, i) => (
                                            <motion.div
                                                key={i}
                                                className="flex items-center justify-between p-4 rounded-xl bg-muted/30"
                                                initial={{ opacity: 0, x: 20 }}
                                                whileInView={{ opacity: 1, x: 0 }}
                                                transition={{ delay: i * 0.1 }}
                                                viewport={{ once: true }}
                                                whileHover={{ x: 4 }}
                                            >
                                                <span className="text-sm text-foreground">{item.label}</span>
                                                <span className="text-sm font-semibold text-medical-pink">{item.value}</span>
                                            </motion.div>
                                        ))}
                                    </div>
                                </motion.div>
                            </div>
                        </motion.div>
                    </div>
                </div>
            </section>

            {/* CTA Section */}
            <section className="py-24 px-4 sm:px-6 lg:px-8">
                <motion.div
                    className="max-w-4xl mx-auto text-center"
                    initial={{ opacity: 0, y: 20 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                >
                    <motion.div
                        className="relative bg-gradient-to-r from-medical-pink/10 via-card to-medical-blue/10 rounded-3xl border border-border/50 p-12 overflow-hidden"
                        whileHover={{ scale: 1.01 }}
                        transition={{ type: "spring", stiffness: 200 }}
                    >
                        <div className="absolute top-0 left-1/4 w-64 h-64 bg-medical-pink/20 rounded-full blur-3xl" />
                        <div className="absolute bottom-0 right-1/4 w-64 h-64 bg-medical-blue/20 rounded-full blur-3xl" />
                        <div className="relative z-10">
                            <Clock className="h-12 w-12 text-medical-pink mx-auto mb-6" />
                            <h2 className="text-3xl sm:text-4xl font-bold text-foreground mb-4">
                                Experience GOTHAM in Action
                            </h2>
                            <p className="text-muted-foreground mb-8 max-w-xl mx-auto">
                                Explore our AI-powered maternal health risk assessment system with a live demo
                                or learn more about the technical implementation.
                            </p>
                            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
                                <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.98 }}>
                                    <Button
                                        size="lg"
                                        onClick={() => navigate("/doctor/signup")}
                                        className="group bg-gradient-to-r from-medical-pink to-medical-blue hover:opacity-90 text-white shadow-xl shadow-medical-pink/30 px-8"
                                    >
                                        <span className="flex items-center">
                                            Get Started
                                            <ArrowRight className="ml-2 h-4 w-4 group-hover:translate-x-1 transition-transform" />
                                        </span>
                                    </Button>
                                </motion.div>
                                <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.98 }}>
                                    <Button
                                        size="lg"
                                        variant="outline"
                                        onClick={() => document.getElementById('features')?.scrollIntoView({ behavior: 'smooth' })}
                                        className="border-border/50 hover:bg-card/50"
                                    >
                                        Learn More
                                    </Button>
                                </motion.div>
                            </div>
                        </div>
                    </motion.div>
                </motion.div>
            </section>

            {/* Footer */}
            <footer className="bg-gradient-to-b from-[hsl(200,45%,14%)] to-[hsl(200,45%,9%)] px-4 sm:px-6 lg:px-8 pt-8 pb-6">
                <div className="max-w-7xl mx-auto">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-6">
                        {/* Brand */}
                        <div>
                            <motion.div className="flex items-center gap-3 mb-3" whileHover={{ scale: 1.02 }}>
                                <div className="relative">
                                    <div className="absolute inset-0 bg-gradient-to-br from-medical-pink to-medical-blue rounded-lg blur-md opacity-20 animate-glow-pulse" />
                                    <div className="relative p-1 rounded-lg">
                                        <img src="/logo.png" alt="GOTHAM Logo" className="h-7 w-7 object-contain" />
                                    </div>
                                </div>
                                <span className="text-lg font-bold bg-gradient-to-r from-medical-pink to-medical-blue bg-clip-text text-transparent">
                                    GOTHAM
                                </span>
                            </motion.div>
                            <p className="text-sm text-white/50 leading-relaxed">
                                AI-Powered Antenatal Care.<br />
                                A research prototype for OB/GYN clinics.
                            </p>
                        </div>

                        {/* Quick Links */}
                        <div>
                            <h4 className="text-xs font-semibold text-white/70 mb-4 uppercase tracking-wider">Quick Links</h4>
                            <ul className="space-y-2">
                                {[
                                    { label: "Doctor Login", action: () => navigate("/doctor/login") },
                                    { label: "Patient Portal", action: () => navigate("/patient/login") },
                                    { label: "Get Started", action: () => navigate("/doctor/signup") },
                                ].map((item) => (
                                    <li key={item.label}>
                                        <motion.button
                                            onClick={item.action}
                                            className="text-sm text-white/50 hover:text-white transition-colors"
                                            whileHover={{ x: 4 }}
                                        >
                                            {item.label}
                                        </motion.button>
                                    </li>
                                ))}
                            </ul>
                        </div>

                        {/* Legal */}
                        <div>
                            <h4 className="text-xs font-semibold text-white/70 mb-4 uppercase tracking-wider">Legal</h4>
                            <ul className="space-y-2">
                                <li>
                                    <motion.button onClick={() => setShowPrivacy(true)}
                                        className="text-sm text-white/50 hover:text-white transition-colors"
                                        whileHover={{ x: 4 }}>
                                        Privacy Policy
                                    </motion.button>
                                </li>
                                <li>
                                    <motion.button onClick={() => setShowTerms(true)}
                                        className="text-sm text-white/50 hover:text-white transition-colors"
                                        whileHover={{ x: 4 }}>
                                        Terms of Service
                                    </motion.button>
                                </li>
                                <li>
                                    <motion.button onClick={() => setShowContact(true)}
                                        className="text-sm text-white/50 hover:text-white transition-colors"
                                        whileHover={{ x: 4 }}>
                                        Contact
                                    </motion.button>
                                </li>
                            </ul>
                        </div>
                    </div>

                    <div className="border-t border-white/10 pt-6 text-center">
                        <p className="text-xs text-white/30">© 2026 GOTHAM. All rights reserved.</p>
                    </div>
                </div>
            </footer>

            {/* Privacy Policy Modal */}
            <AnimatePresence>
                {showPrivacy && (
                    <motion.div
                        className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm"
                        initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                        onClick={() => setShowPrivacy(false)}
                    >
                        <motion.div
                            className="relative bg-card rounded-2xl border border-border/50 shadow-2xl w-full max-w-lg max-h-[80vh] overflow-y-auto p-8"
                            initial={{ opacity: 0, y: 20, scale: 0.97 }}
                            animate={{ opacity: 1, y: 0, scale: 1 }}
                            exit={{ opacity: 0, y: 10, scale: 0.97 }}
                            onClick={(e) => e.stopPropagation()}
                        >
                            <h2 className="text-xl font-bold bg-gradient-to-r from-medical-pink to-medical-blue bg-clip-text text-transparent mb-1">Privacy Policy</h2>
                            <p className="text-xs text-muted-foreground mb-6">Last updated: June 2026</p>

                            <div className="space-y-5 text-sm text-muted-foreground leading-relaxed">
                                <div>
                                    <h3 className="font-semibold text-foreground mb-1">Data We Collect</h3>
                                    <p>We collect account information (name, email, professional credentials), patient health records entered by clinicians (vitals, CBC, CTG readings, ultrasound images), and appointment data. Patients' personal identifiers are stored only to support their assigned doctor's workflow.</p>
                                </div>
                                <div>
                                    <h3 className="font-semibold text-foreground mb-1">How We Use Your Data</h3>
                                    <p>Data is used exclusively to power clinical assessments, generate risk predictions, and facilitate appointment scheduling. We do not use patient data for advertising, profiling, or any purpose outside direct clinical support.</p>
                                </div>
                                <div>
                                    <h3 className="font-semibold text-foreground mb-1">Storage & Security</h3>
                                    <p>Health records are stored in an encrypted Neon PostgreSQL database. Ultrasound images are stored via Cloudinary with access-controlled URLs. All API traffic is authenticated via short-lived JWT tokens.</p>
                                </div>
                                <div>
                                    <h3 className="font-semibold text-foreground mb-1">Third Parties</h3>
                                    <p>We do not sell or share personal data with third parties. AI inference uses OpenAI/Groq APIs; only de-identified query text is transmitted — no patient identifiers are sent to external LLM providers.</p>
                                </div>
                                <div>
                                    <h3 className="font-semibold text-foreground mb-1">Data Deletion</h3>
                                    <p>To request deletion of your account or patient records, contact the team at the addresses listed on this page. Requests are processed within 14 days.</p>
                                </div>
                            </div>
                            <button onClick={() => setShowPrivacy(false)}
                                className="mt-8 w-full py-2.5 rounded-xl bg-gradient-to-r from-medical-pink to-medical-blue text-white text-sm font-semibold hover:opacity-90 transition-opacity">
                                Close
                            </button>
                        </motion.div>
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Terms of Service Modal */}
            <AnimatePresence>
                {showTerms && (
                    <motion.div
                        className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm"
                        initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                        onClick={() => setShowTerms(false)}
                    >
                        <motion.div
                            className="relative bg-card rounded-2xl border border-border/50 shadow-2xl w-full max-w-lg max-h-[80vh] overflow-y-auto p-8"
                            initial={{ opacity: 0, y: 20, scale: 0.97 }}
                            animate={{ opacity: 1, y: 0, scale: 1 }}
                            exit={{ opacity: 0, y: 10, scale: 0.97 }}
                            onClick={(e) => e.stopPropagation()}
                        >
                            <h2 className="text-xl font-bold bg-gradient-to-r from-medical-pink to-medical-blue bg-clip-text text-transparent mb-1">Terms of Service</h2>
                            <p className="text-xs text-muted-foreground mb-6">Last updated: June 2026</p>

                            <div className="space-y-5 text-sm text-muted-foreground leading-relaxed">
                                <div>
                                    <h3 className="font-semibold text-foreground mb-1">Research Prototype Disclaimer</h3>
                                    <p>GOTHAM is a research prototype developed for academic and investigational purposes. It is not a certified medical device. Clinical outputs must be reviewed and validated by a qualified healthcare professional before influencing patient care decisions.</p>
                                </div>
                                <div>
                                    <h3 className="font-semibold text-foreground mb-1">No Medical Advice</h3>
                                    <p>Risk scores, predictions, and AI-generated reports produced by GOTHAM are decision-support tools only. They do not constitute a medical diagnosis or treatment recommendation. Always defer to the judgment of a licensed clinician.</p>
                                </div>
                                <div>
                                    <h3 className="font-semibold text-foreground mb-1">Account Responsibilities</h3>
                                    <p>You are responsible for maintaining the confidentiality of your credentials and for all activity under your account. Doctor accounts require verification; providing false credentials may result in immediate account termination.</p>
                                </div>
                                <div>
                                    <h3 className="font-semibold text-foreground mb-1">Acceptable Use</h3>
                                    <p>This platform may only be used for lawful clinical or research purposes. You may not attempt to reverse-engineer ML models, extract patient data belonging to other providers, or use the system in any way that violates applicable healthcare data regulations.</p>
                                </div>
                                <div>
                                    <h3 className="font-semibold text-foreground mb-1">Limitation of Liability</h3>
                                    <p>GOTHAM is provided "as is" without warranty of any kind. The development team is not liable for clinical outcomes arising from use of this prototype.</p>
                                </div>
                            </div>
                            <button onClick={() => setShowTerms(false)}
                                className="mt-8 w-full py-2.5 rounded-xl bg-gradient-to-r from-medical-pink to-medical-blue text-white text-sm font-semibold hover:opacity-90 transition-opacity">
                                Close
                            </button>
                        </motion.div>
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Contact Modal */}
            <AnimatePresence>
                {showContact && (
                    <motion.div
                        className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm"
                        initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                        onClick={() => setShowContact(false)}
                    >
                        <motion.div
                            className="relative bg-card rounded-2xl border border-border/50 shadow-2xl w-full max-w-sm p-8"
                            initial={{ opacity: 0, y: 20, scale: 0.97 }}
                            animate={{ opacity: 1, y: 0, scale: 1 }}
                            exit={{ opacity: 0, y: 10, scale: 0.97 }}
                            onClick={(e) => e.stopPropagation()}
                        >
                            <h2 className="text-xl font-bold bg-gradient-to-r from-medical-pink to-medical-blue bg-clip-text text-transparent mb-2">Contact Us</h2>
                            <p className="text-sm text-muted-foreground mb-6">Reach out to the GOTHAM development team.</p>
                            <div className="space-y-3">
                                {[
                                    "alimahmud13032@gmail.com",
                                    "eamueed@gmail.com",
                                    "zaiinabsanaullah@gmail.com",
                                ].map((email) => (
                                    <motion.a
                                        key={email}
                                        href={`mailto:${email}`}
                                        className="flex items-center gap-3 p-3 rounded-xl bg-muted/40 hover:bg-muted/70 border border-border/30 hover:border-medical-pink/30 transition-all text-sm text-foreground"
                                        whileHover={{ x: 4 }}
                                    >
                                        <span className="w-2 h-2 rounded-full bg-gradient-to-r from-medical-pink to-medical-blue flex-shrink-0" />
                                        {email}
                                    </motion.a>
                                ))}
                            </div>
                            <button onClick={() => setShowContact(false)}
                                className="mt-6 w-full py-2.5 rounded-xl bg-gradient-to-r from-medical-pink to-medical-blue text-white text-sm font-semibold hover:opacity-90 transition-opacity">
                                Close
                            </button>
                        </motion.div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
};

export default LandingPage;
