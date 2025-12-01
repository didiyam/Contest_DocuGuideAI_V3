// components/AnimatedCheck.tsx
"use client"

import { motion } from "framer-motion"

export function AnimatedCheck() {
    return (
        <motion.svg
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            initial="hidden"
            animate="visible"
        >
            <motion.path
                d="M5 13l4 4L19 7"
                stroke="rgb(34, 211, 238)"
                strokeWidth="2.5"
                strokeLinecap="round"
                strokeLinejoin="round"
                variants={{
                    hidden: { pathLength: 0, opacity: 0 },
                    visible: {
                        pathLength: 1,
                        opacity: 1,
                        transition: {
                            duration: 0.6,
                            ease: "easeOut",
                        },
                    },
                }}
            />
        </motion.svg>
    )
}
