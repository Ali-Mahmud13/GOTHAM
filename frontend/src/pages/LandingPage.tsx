import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { motion, useScroll, useTransform } from "framer-motion";
import { useRef } from "react";
import {
    Brain,
    Users,
    Activity,
    ArrowRight,
    CheckCircle2,
    Sparkles,
    LineChart,
    Clock
} from "lucide-react";

const features = [
    {
        icon: Brain,
        title: "AI-Powered Risk Assessment",
        description: "Machine learning models trained on maternal health data to predict preeclampsia, anemia, and mortality risks.",
        gradient: "from-medical-pink to-medical-pink-light",
    },
    {
        icon: Users,
        title: "Multi-Agent RAG System",
        description: "LangGraph-orchestrated agents with retrieval-augmented generation for evidence-based medical recommendations.",
        gradient: "from-medical-blue to-medical-blue-light",
    },
    {
        icon: Sparkles,
        title: "Clinical Notes Extraction",
        description: "AI-powered extraction of structured data from free-text clinical notes using large language models.",
        gradient: "from-medical-pink to-medical-blue",
    },
    {
        icon: LineChart,
        title: "Explainable AI",
        description: "Transparent risk predictions with feature importance analysis and natural language explanations.",
        gradient: "from-medical-blue to-medical-pink",
    },
];

const stats = [
    { value: "98%", label: "Model Accuracy" },
    { value: "3", label: "Risk Models" },
    { value: "RAG", label: "Knowledge Base" },
    { value: "LangGraph", label: "Multi-Agent" },
];

const steps = [
    {
        number: "01",
        title: "Patient Data Entry",
        description: "Enter patient information manually or extract from clinical notes using AI.",
    },
    {
        number: "02",
        title: "Multi-Agent Analysis",
        description: "LangGraph orchestrator coordinates specialized agents for data processing and RAG retrieval.",
    },
    {
        number: "03",
        title: "Risk Prediction",
        description: "ML models predict preeclampsia, anemia, and mortality risks with confidence scores.",
    },
    {
        number: "04",
        title: "Explainable Results",
        description: "View risk classifications with AI-generated explanations and management recommendations.",
    },
];

export const LandingPage = () => {
    const navigate = useNavigate();
    const heroRef = useRef(null);
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
                                    onClick={() => navigate("/login")}
                                    variant="outline"
                                    className="border-border/50 hover:bg-card/50"
                                >
                                    Login
                                </Button>
                            </motion.div>
                            <motion.div
                                whileHover={{ scale: 1.05 }}
                                whileTap={{ scale: 0.95 }}
                            >
                                <Button
                                    onClick={() => navigate("/signup")}
                                    className="relative overflow-hidden bg-gradient-to-r from-medical-pink to-medical-blue hover:opacity-90 text-white shadow-lg shadow-medical-pink/25 group"
                                >
                                    <span className="relative z-10">Sign Up</span>
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
                            maternal health risks with explainable AI insights.
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
                                    onClick={() => navigate("/login")}
                                    className="group bg-gradient-to-r from-medical-pink to-medical-blue hover:opacity-90 text-white shadow-xl shadow-medical-pink/30 px-8"
                                >
                                    <span className="flex items-center">
                                        Try Demo
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
                                Research
                            </motion.span>
                            <h2 className="text-3xl sm:text-4xl font-bold text-foreground mb-6">
                                Research{" "}
                                <span className="bg-gradient-to-r from-medical-pink to-medical-blue bg-clip-text text-transparent">
                                    Contributions
                                </span>
                            </h2>
                            <p className="text-muted-foreground mb-8">
                                GOTHAM demonstrates the integration of multiple AI technologies for improved maternal health outcomes
                                through intelligent risk prediction and explainable recommendations.
                            </p>
                            <ul className="space-y-4">
                                {[
                                    "Multi-agent system architecture using LangGraph",
                                    "RAG-based medical knowledge retrieval",
                                    "Three specialized ML models for maternal health",
                                    "Explainable AI with feature importance analysis",
                                    "Automated clinical notes extraction using LLMs",
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
                                            <Users className="h-6 w-6 text-white" />
                                        </motion.div>
                                        <div>
                                            <h3 className="font-semibold text-foreground">Technical Innovation</h3>
                                            <p className="text-sm text-muted-foreground">Multi-agent AI architecture</p>
                                        </div>
                                    </div>
                                    <div className="space-y-4">
                                        {[
                                            { label: "Model Accuracy", value: "98%" },
                                            { label: "Agents in System", value: "4" },
                                            { label: "Risk Models", value: "3" },
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
                                        onClick={() => navigate("/login")}
                                        className="group bg-gradient-to-r from-medical-pink to-medical-blue hover:opacity-90 text-white shadow-xl shadow-medical-pink/30 px-8"
                                    >
                                        <span className="flex items-center">
                                            Try Demo
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
            <footer className="py-12 px-4 sm:px-6 lg:px-8 border-t border-border/50">
                <div className="max-w-7xl mx-auto">
                    <div className="flex flex-col md:flex-row items-center justify-between gap-6">
                        <motion.div
                            className="flex items-center gap-3"
                            whileHover={{ scale: 1.02 }}
                        >
                            <div className="relative">
                                <div className="absolute inset-0 bg-gradient-to-br from-medical-pink to-medical-blue rounded-lg blur-md opacity-20 animate-glow-pulse" />
                                <div className="relative p-1 rounded-lg">
                                    <img src="/logo.png" alt="GOTHAM Logo" className="h-6 w-6 object-contain" />
                                </div>
                            </div>
                            <span className="font-bold bg-gradient-to-r from-medical-pink to-medical-blue bg-clip-text text-transparent">
                                GOTHAM
                            </span>
                        </motion.div>
                        <div className="flex items-center gap-8 text-sm text-muted-foreground">
                            {["Privacy Policy", "Terms of Service", "Contact"].map((item) => (
                                <motion.a
                                    key={item}
                                    href="#"
                                    className="hover:text-foreground transition-colors"
                                    whileHover={{ y: -2 }}
                                >
                                    {item}
                                </motion.a>
                            ))}
                        </div>
                        <p className="text-sm text-muted-foreground">
                            © 2024 GOTHAM. All rights reserved.
                        </p>
                    </div>
                </div>
            </footer>
        </div>
    );
};

export default LandingPage;
