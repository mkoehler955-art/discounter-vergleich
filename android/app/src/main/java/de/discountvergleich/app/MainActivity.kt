
package de.discountvergleich.app

import android.os.Bundle
import android.graphics.Typeface
import android.view.ViewGroup
import android.widget.*
import androidx.appcompat.app.AppCompatActivity
import org.json.JSONArray
import java.net.HttpURLConnection
import java.net.URL
import java.util.Locale
import kotlin.concurrent.thread

data class Offer(val store:String,val product:String,val price:Double,val pack:String,val unit:Double?)

class MainActivity: AppCompatActivity() {
    private val apiBase = "http://10.0.2.2:8000"
    private lateinit var search:EditText
    private lateinit var box:LinearLayout
    private lateinit var status:TextView

    override fun onCreate(b:Bundle?) { super.onCreate(b); ui(); load("") }

    private fun ui() {
        val scroll=ScrollView(this)
        val root=LinearLayout(this).apply{orientation=LinearLayout.VERTICAL;setPadding(28,30,28,40)}
        root.addView(TextView(this).apply{text="🛒 Discounter-Vergleich";textSize=28f;typeface=Typeface.DEFAULT_BOLD})
        root.addView(TextView(this).apply{text="Live-Angebote vergleichen";textSize=16f;setPadding(0,5,0,18)})
        search=EditText(this).apply{hint="Produkt suchen, z. B. Milch";singleLine=true}
        root.addView(search, lp())
        root.addView(Button(this).apply{text="🔎 Preise vergleichen";setOnClickListener{load(search.text.toString())}},lp())
        root.addView(Button(this).apply{text="🔄 Angebote aktualisieren";setOnClickListener{refresh()}},lp())
        status=TextView(this).apply{textSize=15f;setPadding(0,10,0,12)}
        root.addView(status)
        box=LinearLayout(this).apply{orientation=LinearLayout.VERTICAL};root.addView(box)
        root.addView(TextView(this).apply{text="\n📍 Region: Eisleben / Seegebiet";textSize=15f})
        scroll.addView(root);setContentView(scroll)
    }
    private fun lp()=LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT,ViewGroup.LayoutParams.WRAP_CONTENT).apply{bottomMargin=10}

    private fun get(path:String):String {
        val c=URL(apiBase+path).openConnection() as HttpURLConnection
        c.connectTimeout=15000;c.readTimeout=20000
        return c.inputStream.bufferedReader().readText()
    }
    private fun load(q:String) {
        status.text="Angebote werden geladen …"
        thread {
            try {
                val arr=JSONArray(get("/offers?q="+java.net.URLEncoder.encode(q,"UTF-8")))
                val list=mutableListOf<Offer>()
                for(i in 0 until arr.length()){
                    val x=arr.getJSONObject(i)
                    list.add(Offer(x.getString("store"),x.getString("product"),x.getDouble("price"),x.optString("pack"),if(x.isNull("unit_price"))null else x.getDouble("unit_price")))
                }
                runOnUiThread{render(list)}
            } catch(e:Exception){runOnUiThread{status.text="Backend nicht erreichbar. Prüfe die Server-Adresse."}}
        }
    }
    private fun refresh(){
        status.text="Aktualisiere Händlerangebote …"
        thread {
            try { get("/refresh"); runOnUiThread{load(search.text.toString())} }
            catch(e:Exception){runOnUiThread{status.text="Aktualisierung fehlgeschlagen: "+e.message}}
        }
    }
    private fun render(list:List<Offer>){
        box.removeAllViews()
        status.text="${list.size} Treffer – günstigster Preis zuerst."
        list.take(100).forEachIndexed{idx,o->
            val t=TextView(this).apply{
                text=(if(idx==0)"🏆 " else "")+"${o.store}   ${String.format(Locale.GERMANY,"%.2f €",o.price)}\n${o.product}"+(if(o.pack.isNotBlank())" • ${o.pack}" else "")
                textSize=if(idx==0)19f else 17f
                typeface=if(idx==0)Typeface.DEFAULT_BOLD else Typeface.DEFAULT
                setPadding(18,18,18,18)
            }
            box.addView(t,lp())
        }
    }
}
