import React from 'react';
import { motion } from 'framer-motion';

/**
 * MovieSkeleton — Premium shimmer loading placeholder.
 * Use count prop to control how many skeletons to show.
 */
const shimmer = {
  hidden: { backgroundPosition: '-200% 0' },
  visible: {
    backgroundPosition: '200% 0',
    transition: { repeat: Infinity, duration: 1.5, ease: 'linear' },
  },
};

function SkeletonCard({ index }) {
  return (
    <div
      className="min-w-[140px] lg:min-w-[220px] aspect-[2/3] rounded-xl overflow-hidden relative"
      style={{ animationDelay: `${index * 80}ms` }}
    >
      {/* Shimmer background */}
      <motion.div
        variants={shimmer}
        initial="hidden"
        animate="visible"
        className="absolute inset-0 rounded-xl"
        style={{
          background: 'linear-gradient(90deg, #1c1c1e 25%, #2a2a2e 50%, #1c1c1e 75%)',
          backgroundSize: '200% 100%',
        }}
      />

      {/* Bottom info skeleton */}
      <div className="absolute bottom-0 left-0 right-0 p-3 space-y-2">
        {/* Title bar */}
        <div className="h-3 w-3/4 rounded-full bg-white/5" />
        {/* Stars bar */}
        <div className="flex gap-1">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="w-3 h-3 rounded-full bg-white/5" />
          ))}
        </div>
      </div>

      {/* Subtle border */}
      <div className="absolute inset-0 rounded-xl border border-white/[0.04]" />
    </div>
  );
}

export default function MovieSkeleton({ count = 6 }) {
  return (
    <div className="flex space-x-4 overflow-hidden py-6">
      {[...Array(count)].map((_, i) => (
        <SkeletonCard key={i} index={i} />
      ))}
    </div>
  );
}
