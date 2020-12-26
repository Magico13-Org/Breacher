using System;
using System.Collections.Generic;

namespace BreacherFrontend
{
    public class BreachCache
    {
        private Dictionary<string, BreachResponse> _cache = new Dictionary<string, BreachResponse>();

        public string StoreBreachResponse(BreachResponse toStore)
        {
            string key = Guid.NewGuid().ToString();

            _cache[key] = toStore;
            return key;
        }

        public BreachResponse GetBreachResponse(string key, bool remove=false)
        {
            BreachResponse response = null;
            if (_cache.TryGetValue(key, out response))
            {
                if (remove)
                {
                    _cache.Remove(key);
                }
            }
            return response;
        }
    }
}
