using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Linq;

namespace DysonMCP
{
    /// <summary>
    /// Collects and aggregates factory metrics from Harmony patches.
    /// Thread-safe singleton accessed by patches and the main plugin.
    /// </summary>
    public class MetricsCollector
    {
        /// <summary>
        /// Singleton instance set by the plugin.
        /// </summary>
        public static MetricsCollector Instance { get; set; }

        private readonly int _updateFrequencyHz;
        private readonly object _lock = new object();

        // Accumulators keyed by (planetId, entityId)
        private readonly ConcurrentDictionary<(int, int), ProductionAccumulator> _productionAccumulators;
        private readonly ConcurrentDictionary<int, PowerAccumulator> _powerAccumulators;
        private readonly ConcurrentDictionary<(int, int), BeltAccumulator> _beltAccumulators;

        // Last collected snapshot for caching
        private MetricsSnapshot _lastSnapshot;
        private long _lastCollectionTick;

        /// <summary>
        /// Minimum ticks between full metric collections.
        /// </summary>
        private int CollectionIntervalTicks => 60 / _updateFrequencyHz;

        public MetricsCollector(int updateFrequencyHz = 1)
        {
            _updateFrequencyHz = Math.Max(1, Math.Min(60, updateFrequencyHz));
            _productionAccumulators = new ConcurrentDictionary<(int, int), ProductionAccumulator>();
            _powerAccumulators = new ConcurrentDictionary<int, PowerAccumulator>();
            _beltAccumulators = new ConcurrentDictionary<(int, int), BeltAccumulator>();
        }

        #region Static Recording Methods (Called by Patches)

        /// <summary>
        /// Record production output from an assembler/smelter.
        /// Called by ProductionPatch when items are produced.
        /// </summary>
        public static void RecordProduction(
            int planetId,
            int assemblerId,
            int recipeId,
            int protoId,
            int itemsProduced,
            long gameTick,
            bool inputStarved,
            bool outputBlocked,
            float powerLevel)
        {
            if (Instance == null) return;

            var key = (planetId, assemblerId);
            Instance._productionAccumulators.AddOrUpdate(
                key,
                _ => new ProductionAccumulator
                {
                    PlanetId = planetId,
                    AssemblerId = assemblerId,
                    RecipeId = recipeId,
                    TotalProduced = itemsProduced,
                    FirstTick = gameTick,
                    LastTick = gameTick,
                    InputStarved = inputStarved,
                    OutputBlocked = outputBlocked,
                    LastPowerLevel = powerLevel
                },
                (_, acc) =>
                {
                    acc.TotalProduced += itemsProduced;
                    acc.LastTick = gameTick;
                    acc.InputStarved = inputStarved;
                    acc.OutputBlocked = outputBlocked;
                    acc.LastPowerLevel = powerLevel;
                    return acc;
                });
        }

        /// <summary>
        /// Record power grid state for a planet.
        /// Called by PowerPatch each tick.
        /// </summary>
        public static void RecordPower(
            int planetId,
            long generationEnergyPerTick,
            long consumptionEnergyPerTick,
            long accumulatorCurrent,
            long accumulatorMax,
            int generatorCount,
            int consumerCount,
            int accumulatorCount,
            long gameTick)
        {
            if (Instance == null) return;

            Instance._powerAccumulators.AddOrUpdate(
                planetId,
                _ => new PowerAccumulator
                {
                    PlanetId = planetId,
                    TotalGeneration = generationEnergyPerTick,
                    TotalConsumption = consumptionEnergyPerTick,
                    AccumulatorCurrent = accumulatorCurrent,
                    AccumulatorMax = accumulatorMax,
                    GeneratorCount = generatorCount,
                    ConsumerCount = consumerCount,
                    AccumulatorCount = accumulatorCount,
                    LastUpdateTick = gameTick
                },
                (_, acc) =>
                {
                    acc.TotalGeneration = generationEnergyPerTick;
                    acc.TotalConsumption = consumptionEnergyPerTick;
                    acc.AccumulatorCurrent = accumulatorCurrent;
                    acc.AccumulatorMax = accumulatorMax;
                    acc.GeneratorCount = generatorCount;
                    acc.ConsumerCount = consumerCount;
                    acc.AccumulatorCount = accumulatorCount;
                    acc.LastUpdateTick = gameTick;
                    return acc;
                });
        }

        /// <summary>
        /// Record belt throughput sample.
        /// Called by LogisticsPatch periodically.
        /// </summary>
        public static void RecordBeltThroughput(
            int planetId,
            int beltId,
            int itemType,
            int itemCount,
            int bufferLength,
            float maxThroughput,
            long gameTick)
        {
            if (Instance == null) return;

            var key = (planetId, beltId);
            Instance._beltAccumulators.AddOrUpdate(
                key,
                _ => new BeltAccumulator
                {
                    PlanetId = planetId,
                    BeltId = beltId,
                    ItemType = itemType,
                    TotalItems = itemCount,
                    SampleCount = 1,
                    MaxThroughput = maxThroughput,
                    BufferLength = bufferLength,
                    FirstTick = gameTick,
                    LastTick = gameTick
                },
                (_, acc) =>
                {
                    acc.TotalItems += itemCount;
                    acc.SampleCount++;
                    acc.ItemType = itemType;
                    acc.MaxThroughput = maxThroughput;
                    acc.BufferLength = bufferLength;
                    acc.LastTick = gameTick;
                    return acc;
                });
        }

        #endregion

        #region Metrics Collection

        /// <summary>
        /// Collect current metrics snapshot.
        /// Aggregates all accumulated data and resets accumulators.
        /// </summary>
        public MetricsSnapshot CollectMetrics()
        {
            long currentTick = GetCurrentGameTick();

            lock (_lock)
            {
                var snapshot = new MetricsSnapshot
                {
                    Timestamp = DateTimeOffset.UtcNow.ToUnixTimeSeconds(),
                    GameTick = currentTick
                };

                // Collect power metrics per planet
                foreach (var kvp in _powerAccumulators)
                {
                    int planetId = kvp.Key;
                    var powerAcc = kvp.Value;

                    if (!snapshot.Planets.TryGetValue(planetId, out var planetMetrics))
                    {
                        planetMetrics = new PlanetMetrics
                        {
                            PlanetId = planetId,
                            PlanetName = GetPlanetName(planetId)
                        };
                        snapshot.Planets[planetId] = planetMetrics;
                    }

                    planetMetrics.Power = new PowerMetrics
                    {
                        GenerationEnergyPerTick = powerAcc.TotalGeneration,
                        ConsumptionEnergyPerTick = powerAcc.TotalConsumption,
                        AccumulatorCurrentEnergy = powerAcc.AccumulatorCurrent,
                        AccumulatorMaxEnergy = powerAcc.AccumulatorMax,
                        GeneratorCount = powerAcc.GeneratorCount,
                        ConsumerCount = powerAcc.ConsumerCount,
                        AccumulatorCount = powerAcc.AccumulatorCount
                    };
                }

                // Collect production metrics
                foreach (var kvp in _productionAccumulators)
                {
                    int planetId = kvp.Key.Item1;
                    var prodAcc = kvp.Value;

                    if (!snapshot.Planets.TryGetValue(planetId, out var planetMetrics))
                    {
                        planetMetrics = new PlanetMetrics
                        {
                            PlanetId = planetId,
                            PlanetName = GetPlanetName(planetId)
                        };
                        snapshot.Planets[planetId] = planetMetrics;
                    }

                    planetMetrics.Production.Add(new ProductionMetric
                    {
                        AssemblerId = prodAcc.AssemblerId,
                        RecipeId = prodAcc.RecipeId,
                        ProtoId = prodAcc.RecipeId, // Will be updated with actual proto
                        ItemsProduced = prodAcc.TotalProduced,
                        ProductionRate = prodAcc.CalculateRate(),
                        InputStarved = prodAcc.InputStarved,
                        OutputBlocked = prodAcc.OutputBlocked,
                        PowerLevel = prodAcc.LastPowerLevel
                    });
                }

                // Collect belt metrics
                foreach (var kvp in _beltAccumulators)
                {
                    int planetId = kvp.Key.Item1;
                    var beltAcc = kvp.Value;

                    if (!snapshot.Planets.TryGetValue(planetId, out var planetMetrics))
                    {
                        planetMetrics = new PlanetMetrics
                        {
                            PlanetId = planetId,
                            PlanetName = GetPlanetName(planetId)
                        };
                        snapshot.Planets[planetId] = planetMetrics;
                    }

                    planetMetrics.Belts.Add(new BeltMetric
                    {
                        BeltId = beltAcc.BeltId,
                        ItemType = beltAcc.ItemType,
                        Throughput = beltAcc.CalculateThroughput(),
                        MaxThroughput = beltAcc.MaxThroughput,
                        ItemCount = beltAcc.TotalItems / Math.Max(1, beltAcc.SampleCount),
                        BufferLength = beltAcc.BufferLength
                    });
                }

                // Reset production and belt accumulators for next collection period
                ResetAccumulators(currentTick);

                _lastSnapshot = snapshot;
                _lastCollectionTick = currentTick;

                return snapshot;
            }
        }

        /// <summary>
        /// Get current metrics without resetting accumulators.
        /// Returns cached snapshot if called within collection interval.
        /// </summary>
        public MetricsSnapshot GetCurrentMetrics()
        {
            long currentTick = GetCurrentGameTick();

            if (_lastSnapshot != null &&
                (currentTick - _lastCollectionTick) < CollectionIntervalTicks)
            {
                return _lastSnapshot;
            }

            return CollectMetrics();
        }

        /// <summary>
        /// Reset accumulators for next collection period.
        /// </summary>
        private void ResetAccumulators(long currentTick)
        {
            // Reset production accumulators
            foreach (var acc in _productionAccumulators.Values)
            {
                acc.TotalProduced = 0;
                acc.FirstTick = currentTick;
            }

            // Reset belt accumulators
            foreach (var acc in _beltAccumulators.Values)
            {
                acc.TotalItems = 0;
                acc.SampleCount = 0;
                acc.FirstTick = currentTick;
            }

            // Power accumulators don't need reset - they represent current state
        }

        /// <summary>
        /// Clear all accumulated data.
        /// </summary>
        public void ClearAll()
        {
            _productionAccumulators.Clear();
            _powerAccumulators.Clear();
            _beltAccumulators.Clear();
            _lastSnapshot = null;
            _lastCollectionTick = 0;
        }

        #endregion

        #region Game Data Access

        /// <summary>
        /// Get current game tick from DSP GameMain.
        /// </summary>
        private static long GetCurrentGameTick()
        {
            try
            {
                // Access DSP's GameMain.gameTick
                var gameMainType = Type.GetType("GameMain, Assembly-CSharp");
                if (gameMainType != null)
                {
                    var gameTickField = gameMainType.GetField("gameTick",
                        System.Reflection.BindingFlags.Public | System.Reflection.BindingFlags.Static);
                    if (gameTickField != null)
                    {
                        return (long)gameTickField.GetValue(null);
                    }
                }
            }
            catch
            {
                // Fallback if reflection fails
            }

            return DateTimeOffset.UtcNow.ToUnixTimeMilliseconds();
        }

        /// <summary>
        /// Get planet name from DSP GameMain.
        /// </summary>
        private static string GetPlanetName(int planetId)
        {
            try
            {
                // Access DSP's GameMain.galaxy.PlanetById(planetId).displayName
                var gameMainType = Type.GetType("GameMain, Assembly-CSharp");
                if (gameMainType != null)
                {
                    var galaxyField = gameMainType.GetField("galaxy",
                        System.Reflection.BindingFlags.Public | System.Reflection.BindingFlags.Static);
                    if (galaxyField != null)
                    {
                        var galaxy = galaxyField.GetValue(null);
                        if (galaxy != null)
                        {
                            var planetByIdMethod = galaxy.GetType().GetMethod("PlanetById");
                            if (planetByIdMethod != null)
                            {
                                var planet = planetByIdMethod.Invoke(galaxy, new object[] { planetId });
                                if (planet != null)
                                {
                                    var displayNameProp = planet.GetType().GetProperty("displayName");
                                    if (displayNameProp != null)
                                    {
                                        return displayNameProp.GetValue(planet) as string ?? $"Planet {planetId}";
                                    }
                                }
                            }
                        }
                    }
                }
            }
            catch
            {
                // Fallback if reflection fails
            }

            return $"Planet {planetId}";
        }

        #endregion
    }
}
