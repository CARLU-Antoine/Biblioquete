import {useState} from 'react';
import {StyleSheet,Text,View,TextInput,Image,Pressable} from 'react-native';
import {Dimensions} from 'react-native';
import {FontAwesome,MaterialIcons} from '@expo/vector-icons';
import useIsWeb from '../techniqueTools/useInWeb';
export const {width: screenWidth} = Dimensions.get("window");
export const {height: screenHeight} = Dimensions.get("window");


export default function MainPage(props){
    const [emailPretension,setEmailPretension] = useState("");
    const isWeb = useIsWeb();

    let books = [];
    for(let i=0;i<5;i++){
      books.push(
      <View style={{width:"100%",height:isWeb ? screenHeight*0.19 : screenHeight*0.17,flexDirection:"row",backgroundColor:"white",alignItems:"center",paddingHorizontal:"2%"}}>
        <Image
          source={require("../assets/pg791.cover.medium.jpg")}
          style={{width:screenWidth*0.2,height:screenHeight*0.15}}
        ></Image>
        <View style={{height:"90%",margin:"2%"}}>
          <Text style={{fontSize: 20,fontWeight:"500"}}>Titre</Text>
          <Text style={{fontSize: 10,fontWeight:"300"}}>Auteur (date - date)</Text>
          <Text style={{fontSize: 10,fontWeight:"300"}}>Préambule - Eo adducta re per Isauriam, rege 
            Persarum bellis finitimis inligato repellenteque
            a conlimitiis suis ferocissimas gentes, quae 
            mente quadam versabili hostiliter eum saep...</Text>
        </View>
      </View>)
    }

    return (
    <View style={styles.container}>
      <View style={{width:"100%",height:isWeb ? screenHeight*0.09 : screenHeight*0.115,flexDirection:"row",alignItems:"flex-end",justifyContent:"space-between",paddingTop:"0%",paddingHorizontal:"4%",paddingBottom:screenHeight*0.02,borderBottomWidth:0.5,borderColor:"black",backgroundColor:"white"}}>
        <Text style={{fontSize: screenHeight*0.03,fontWeight:"500"}}>Bibliothèque</Text>
        <View>
            <TextInput
                maxLength={30}
                onChangeText={(text)=>setEmailPretension(text)}
                style={{width:screenWidth*0.54,height:screenHeight*0.040,borderWidth:0.5,maxWidth:"550px",borderRadius:10,fontSize:13}}
            />
            {/* <View style={{borderWidth:0.5}}>
                <FontAwesome name="gear" size={screenWidth*0.06} color="black" style={{paddingTop:'5%',marginLeft:'6%'}} onPress={()=>console.log("okkkk")}/>
            </View> */}
        </View>
      </View>
        {books}
      {isWeb ? 
        <></>
      :       
      <View style={{flexDirection:"row",justifyContent:"space-around",borderWidth:0.5,borderColor:"black",backgroundColor:"white",width:"100%",height:screenHeight*0.077,alignItems:"center"}}>
        <View>
          <Text style={{fontSize:12,marginHorizontal:"13%"}}>Aucune recherche lancée</Text>
        </View>
        <View style={{alignSelf:"flex-end",justifyContent:"flex-end"}}>
          <Text style={{fontSize:10}}>1/270</Text>
        </View>
        <View style={{flexDirection:"row"}}>
          <Pressable
            onPress={() => console.log("Pressé !")}
            style={({ pressed }) => ({
              backgroundColor:"white",
              borderWidth: 0.5,
              padding: 5,
              borderRadius: 25,
              alignItems:"flex-end"
            })}
          >
            <MaterialIcons name="arrow-back-ios" size={screenWidth * 0.06} color="black" style={{padding:"1%", margin:"1%"}}/>
            </Pressable>
            <Pressable
              onPress={() => console.log("Pressé !")}
              style={({ pressed }) => ({
                backgroundColor:"white",
                borderWidth: 0.5,
                padding: 5,
                borderRadius: 25,
                alignItems:"flex-end"
              })}
            >
              <MaterialIcons  name="arrow-forward-ios" size={screenWidth * 0.06} color="black" style={{padding:"1%", margin:"1%"}}/>
            </Pressable>

        </View>
      </View>}
    </View>
    );
}

const styles = StyleSheet.create({
  container:{
      flex:1,
      backgroundColor: 'white',
      alignItems: 'center',
      flexDirection:"column",
      justifyContent:"space-between",
  },
  card: {
      alignItems:'center',
      justifyContent:'center',
      backgroundColor:"#EAEAEA",
      borderRadius:4,
  }
});
