import { motion } from 'framer-motion';

export default function About() {
  const skills = ['React', 'TypeScript', 'Next.js', 'Tailwind', 'Firebase', 'Flutter', 'Supabase'];

  return (
    <section id="about" className="py-32 px-6 max-w-5xl mx-auto">
      <div className="grid md:grid-cols-5 gap-16 items-start">
        <motion.div
          initial={{ opacity: 0, x: -30 }}
          whileInView={{ opacity: 1, x: 0 }}
          viewport={{ once: true, margin: '-100px' }}
          transition={{ duration: 0.6 }}
          className="md:col-span-2"
        >
          <h2 className="text-xs uppercase tracking-[0.2em] font-mono text-neutral-400 dark:text-neutral-500 mb-4">
            01 // Biography
          </h2>
          <h3 className="text-3xl font-bold tracking-tight">About Me</h3>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, x: 30 }}
          whileInView={{ opacity: 1, x: 0 }}
          viewport={{ once: true, margin: '-100px' }}
          transition={{ duration: 0.6, delay: 0.1 }}
          className="md:col-span-3 space-y-6 text-lg font-light leading-relaxed opacity-80"
        >
          <p>
            I am a full-stack engineer focused on creating elegant, highly scannable digital products. I combine clean code architectures with fast visual design to deliver striking web applications.
          </p>
          <p>
            My development pipeline specializes in modular scalability, cross-platform performance execution, and robust backend ecosystems that don't compromise aesthetic integrity.
          </p>

          <div className="pt-8">
            <h4 className="text-xs uppercase tracking-[0.2em] font-mono text-neutral-400 dark:text-neutral-500 mb-6">
              Expertise & Framework Stack
            </h4>
            <div className="flex flex-wrap gap-3">
              {skills.map((skill, index) => (
                <motion.span
                  key={skill}
                  initial={{ opacity: 0, scale: 0.8 }}
                  whileInView={{ opacity: 1, scale: 1 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.3, delay: index * 0.05 }}
                  className="px-4 py-2 border border-neutral-200 dark:border-neutral-800 rounded-full text-sm font-medium bg-neutral-50 dark:bg-neutral-900/50"
                >
                  {skill}
                </motion.span>
              ))}
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}