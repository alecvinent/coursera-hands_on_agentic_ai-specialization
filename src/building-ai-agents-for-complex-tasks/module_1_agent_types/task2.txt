Which classification challenged you the most, and what did you learn from it?

The Hybrid applications—specifically the Real-Time Traffic Route Optimizer—proved to be the most challenging to classify.

The main difficulty stems from the overlap between reactive and deliberative behaviors. At first glance, a route optimizer looks purely deliberative because it calculates complex, multi-stop delivery sequences based on goal constraints. However, because it must also process sudden real-time events (like traffic accidents or sudden road closures) and re-route instantly on the fly, it actively embeds a reactive loop into its broader planning system.

Key Takeaways:

- Real-world systems rarely fit into neat boxes: Purely reactive or purely deliberative architectures are often theoretical extremes; most production-level AI applications in logistics rely on hybrid frameworks.
- Architecture depends on time horizons: The deliberative component operates on a macro level (planning for the entire shift or route), while the reactive component handles micro adjustments (responding to instant sensor inputs or traffic alerts).
- Sensor processing vs. goal processing: Classifying an agent requires looking at how it handles inputs—whether it directly executes a pre-set rule, updates a global plan, or combines both to fulfill its objective efficiently.
