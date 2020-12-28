using System;
using System.Collections.Generic;

namespace BreacherFrontend
{
    public class ResponseCache
    {
        private Dictionary<string, ResponseBase> _cache = new Dictionary<string, ResponseBase>();

        public string StoreResponse(ResponseBase toStore)
        {
            string key = Guid.NewGuid().ToString();

            _cache[key] = toStore;
            return key;
        }

        public T GetResponse<T>(string key, bool remove=false) where T: ResponseBase
        {
            T response = null;
            if (_cache.TryGetValue(key, out ResponseBase responseBase))
            {
                response = responseBase as T;
                if (remove)
                {
                    _cache.Remove(key);
                }
            }
            return response;
        }
    }
}
