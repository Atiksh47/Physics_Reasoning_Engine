import type { SimulationResult, CollisionEvent } from "../api/client";

interface Props {
  explanation: string;
  result: SimulationResult;
}

function CollisionBadge({ c }: { c: CollisionEvent }) {
  return (
    <span className="collision-badge">
      {c.objects.join(" + ")} @ t={c.time.toFixed(2)}s
    </span>
  );
}

export default function ExplanationPanel({ explanation, result }: Props) {
  const { collisions, final_states } = result;

  return (
    <div className="explanation-panel">
      <h3 className="panel-title">Explanation</h3>

      <p className="explanation-text">{explanation}</p>

      {collisions.length > 0 && (
        <div className="collisions-section">
          <span className="section-label">Collisions: </span>
          {collisions.map((c, i) => (
            <CollisionBadge key={i} c={c} />
          ))}
        </div>
      )}

      {Object.keys(final_states).length > 0 && (
        <div className="final-states">
          <span className="section-label">Final states:</span>
          <table className="state-table">
            <thead>
              <tr>
                <th>Object</th>
                <th>Position</th>
                <th>Speed</th>
                <th>Peak speed</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(final_states).map(([name, state]) => {
                const speed = Math.hypot(state.velocity[0], state.velocity[1]);
                return (
                  <tr key={name}>
                    <td>{name}</td>
                    <td>
                      ({state.position[0].toFixed(2)}, {state.position[1].toFixed(2)})
                    </td>
                    <td>{speed.toFixed(2)} m/s</td>
                    <td>{state.peak_velocity.toFixed(2)} m/s</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
